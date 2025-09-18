package main

import (
	"bytes"
	"context"
	"fmt"
	"log"
	"log/slog"
	"math"
	"net/http"
	"os"
	"path/filepath"
	"song-recognition/db"
	"song-recognition/shazam"
	"song-recognition/spotify"
	"song-recognition/utils"
	"song-recognition/wav"
	"strconv"
	"strings"
	"time"

	"github.com/fatih/color"
	"github.com/gofiber/fiber/v3"
	"github.com/gofiber/fiber/v3/middleware/adaptor"
	"github.com/gofiber/fiber/v3/middleware/cors"
	"github.com/gofiber/fiber/v3/middleware/static"
	"github.com/mdobak/go-xerrors"
	"github.com/zishang520/engine.io/v2/types"
	"github.com/zishang520/socket.io/v2/socket"
)

const (
	SONGS_DIR = "songs"
)

var (
	yellow            = color.New(color.FgYellow)
	CORS_ALLOW_ORIGIN = os.Getenv("CORS_ALLOW_ORIGIN")
	SEEK_TUNE_VERSION = os.Getenv("SEEK_TUNE_VERSION")
)

func find(filePath string) {
	wavInfo, err := wav.ReadWavInfo(filePath)
	if err != nil {
		yellow.Println("Error reading wave info:", err)
		return
	}

	samples, err := wav.WavBytesToSamples(wavInfo.Data)
	if err != nil {
		yellow.Println("Error converting to samples:", err)
		return
	}

	matches, searchDuration, err := shazam.FindMatches(samples, wavInfo.Duration, wavInfo.SampleRate)
	if err != nil {
		yellow.Println("Error finding matches:", err)
		return
	}

	if len(matches) == 0 {
		fmt.Println("\nNo match found.")
		fmt.Printf("\nSearch took: %s\n", searchDuration)
		return
	}

	msg := "Matches:"
	topMatches := matches
	if len(matches) >= 20 {
		msg = "Top 20 matches:"
		topMatches = matches[:20]
	}

	fmt.Println(msg)
	for _, match := range topMatches {
		fmt.Printf("\t- %s by %s, score: %.2f\n",
			match.SongTitle, match.SongArtist, match.Score)
	}

	fmt.Printf("\nSearch took: %s\n", searchDuration)
	topMatch := topMatches[0]
	fmt.Printf("\nFinal prediction: %s by %s , score: %.2f\n",
		topMatch.SongTitle, topMatch.SongArtist, topMatch.Score)
}

func download(spotifyURL string) {
	err := utils.CreateFolder(SONGS_DIR)
	if err != nil {
		err := xerrors.New(err)
		logger := utils.GetLogger()
		ctx := context.Background()
		logMsg := fmt.Sprintf("failed to create directory %v", SONGS_DIR)
		logger.ErrorContext(ctx, logMsg, slog.Any("error", err))
	}

	if strings.Contains(spotifyURL, "album") {
		_, err := spotify.DlAlbum(spotifyURL, SONGS_DIR)
		if err != nil {
			yellow.Println("Error: ", err)
		}
	}

	if strings.Contains(spotifyURL, "playlist") {
		_, err := spotify.DlPlaylist(spotifyURL, SONGS_DIR)
		if err != nil {
			yellow.Println("Error: ", err)
		}
	}

	if strings.Contains(spotifyURL, "track") {
		_, err := spotify.DlSingleTrack(spotifyURL, SONGS_DIR)
		if err != nil {
			yellow.Println("Error: ", err)
		}
	}
}

func fingerprintRecognizeHTTPHandler(rw http.ResponseWriter, req *http.Request) {
	// fmt.Println("[HTTP/Fingerprint] Received ", req.ContentLength)
	buf := new(bytes.Buffer)
	buf.ReadFrom(req.Body)
	respBytes := buf.String()

	respString := string(respBytes)
	data := FingerprintDataForRecognition(respString)

	// fmt.Println("[HTTP/Fingerprint] Finished")

	rw.Header().Set("Content-Type", "application/json")
	rw.Write([]byte(data))
}

func audioRecognizeHTTPHandler(rw http.ResponseWriter, req *http.Request) {
	// fmt.Println("[HTTP/Audio] Received ", req.ContentLength)
	buf := new(bytes.Buffer)
	buf.ReadFrom(req.Body)
	respBytes := buf.String()

	respString := string(respBytes)
	data := AudioDataForRecognition(respString)

	// fmt.Println("[HTTP/Audio] Finished")

	rw.Header().Set("Content-Type", "application/json")
	rw.Write([]byte(data))
}

func serve(protocol, port string, prefork bool) {
	server := socket.NewServer(nil, nil)

	server.On("connection", func(clients ...any) {
		client := clients[0].(*socket.Socket)

		client.On("totalSongs", handleTotalSongs(client))
		client.On("newFingerprint", handleNewFingerprint(client))
		client.On("saasFind", func(a ...any) {
			go handleSaaSFind(client)(a...)
		})

		client.On("disconnect", func(a ...any) {
			log.Println(a)
			log.Println("closed")
		})

		client.On("error", func(a ...any) {
			log.Println(a)
		})
	})

	defer server.Close(nil)

	serveHTTP(server, port, prefork)
}

func serveHTTP(socketServer *socket.Server, port string, prefork bool) {

	opts := socket.DefaultServerOptions()

	opts.SetMaxHttpBufferSize(1e9)
	opts.SetAllowUpgrades(false)
	opts.SetPingInterval(5 * time.Second)
	opts.SetPingTimeout(5 * time.Second)
	opts.SetHttpCompression(&types.HttpCompression{})
	opts.SetMaxHttpBufferSize(1e8)

	// ////////////////////////////

	app := fiber.New(fiber.Config{
		BodyLimit: 100 * 1024 * 1024,
	})

	app.Use(cors.New(cors.Config{
		AllowOrigins:     []string{CORS_ALLOW_ORIGIN},
		AllowCredentials: true,
		AllowMethods: []string{
			fiber.MethodGet,
			fiber.MethodPost,
			fiber.MethodHead,
			fiber.MethodPut,
			fiber.MethodDelete,
			fiber.MethodPatch,
			fiber.MethodOptions,
		},
		AllowHeaders: []string{""},
	}))

	app.Get("/*", static.New(fmt.Sprintf("../seek-tune-%s/build", SEEK_TUNE_VERSION)))

	// app.Put("/socket.io", adaptor.HTTPHandler(socketio.ServeHandler(c))) // test
	app.Get("/socket.io", adaptor.HTTPHandler(socketServer.ServeHandler(opts)))
	app.Post("/socket.io", adaptor.HTTPHandler(socketServer.ServeHandler(opts)))

	app.Post("/api/fingerprintRecognize", adaptor.HTTPHandlerFunc(fingerprintRecognizeHTTPHandler))
	app.Post("/api/audioRecognize", adaptor.HTTPHandlerFunc(audioRecognizeHTTPHandler))

	log.Printf("Starting HTTP server on port %v", port)
	app.Listen(":"+port, fiber.ListenConfig{EnablePrefork: prefork})
}

func erase(songsDir string) {
	logger := utils.GetLogger()
	ctx := context.Background()

	// wipe db
	dbClient, err := db.NewDBClient()
	if err != nil {
		msg := fmt.Sprintf("Error creating DB client: %v\n", err)
		logger.ErrorContext(ctx, msg, slog.Any("error", err))
	}

	err = dbClient.DeleteCollection("fingerprints")
	if err != nil {
		msg := fmt.Sprintf("Error deleting collection: %v\n", err)
		logger.ErrorContext(ctx, msg, slog.Any("error", err))
	}

	err = dbClient.DeleteCollection("songs")
	if err != nil {
		msg := fmt.Sprintf("Error deleting collection: %v\n", err)
		logger.ErrorContext(ctx, msg, slog.Any("error", err))
	}

	// delete song files
	err = filepath.Walk(songsDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !info.IsDir() {
			ext := filepath.Ext(path)
			if ext == ".wav" || ext == ".m4a" {
				err := os.Remove(path)
				if err != nil {
					return err
				}
			}
		}
		return nil
	})
	if err != nil {
		msg := fmt.Sprintf("Error walking through directory %s: %v\n", songsDir, err)
		logger.ErrorContext(ctx, msg, slog.Any("error", err))
	}

	fmt.Println("Erase complete")
}

func save(path string, force bool) {
	fileInfo, err := os.Stat(path)
	if err != nil {
		fmt.Printf("Error stating path %v: %v\n", path, err)
		return
	}

	if fileInfo.IsDir() {
		err := filepath.Walk(path, func(filePath string, info os.FileInfo, err error) error {
			if err != nil {
				fmt.Printf("Error walking the path %v: %v\n", filePath, err)
				return err
			}
			// Process only files, skip directories
			if !info.IsDir() {
				err := saveSong(filePath, force)
				if err != nil {
					fmt.Printf("Error saving song (%v): %v\n", filePath, err)
				}
			}
			return nil
		})
		if err != nil {
			fmt.Printf("Error walking the directory %v: %v\n", path, err)
		}
	} else {
		err := saveSong(path, force)
		if err != nil {
			fmt.Printf("Error saving song (%v): %v\n", path, err)
		}
	}
}

func saveSong(filePath string, force bool) error {
	metadata, err := wav.GetMetadata(filePath)
	if err != nil {
		return err
	}

	durationFloat, err := strconv.ParseFloat(metadata.Format.Duration, 64)
	if err != nil {
		return fmt.Errorf("failed to parse duration to float: %v", err)
	}

	tags := metadata.Format.Tags
	track := &spotify.Track{
		Album:    tags["album"],
		Artist:   tags["artist"],
		Title:    tags["title"],
		Duration: int(math.Round(durationFloat)),
	}

	ytID, err := spotify.GetYoutubeId(*track)
	if err != nil && !force {
		return fmt.Errorf("failed to get YouTube ID for song: %v", err)
	}

	fileName := strings.TrimSuffix(filepath.Base(filePath), filepath.Ext(filePath))
	if track.Title == "" {
		// If title is empty, use the file name
		track.Title = fileName
	}

	if track.Artist == "" {
		return fmt.Errorf("no artist found in metadata")
	}

	err = spotify.ProcessAndSaveSong(filePath, track.Title, track.Artist, ytID)
	if err != nil {
		return fmt.Errorf("failed to process or save song: %v", err)
	}

	// Move song in wav format to songs directory
	wavFile := fileName + ".wav"
	sourcePath := filepath.Join(filepath.Dir(filePath), wavFile)
	newFilePath := filepath.Join(SONGS_DIR, wavFile)
	err = utils.MoveFile(sourcePath, newFilePath)
	if err != nil {
		return fmt.Errorf("failed to rename temporary file to output file: %v", err)
	}

	return nil
}
