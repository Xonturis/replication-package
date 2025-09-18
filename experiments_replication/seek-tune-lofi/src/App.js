import React, { useEffect, useState, useRef } from "react";
import io from "socket.io-client";
import Form from "./components/Form";
import Listen from "./components/Listen";
import CarouselSliders from "./components/CarouselSliders";
import { FaMicrophoneLines } from "react-icons/fa6";
import { LiaLaptopSolid } from "react-icons/lia";
import { ToastContainer, toast, Slide } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { MediaRecorder, register } from "extendable-media-recorder";
import { connect } from "extendable-media-recorder-wav-encoder";
import { FFmpeg } from '@ffmpeg/ffmpeg';
import { fetchFile } from '@ffmpeg/util';


import AnimatedNumber from "./components/AnimatedNumber";

const server = process.env.REACT_APP_BACKEND_URL || "http://localhost:5000/";
const wsPlaceholder = server+"api/fingerprintRecognize"
const gowasm = server+"main.wasm"

var socket = io(server, { withCredentials:true });

function App() {
  const uploadRecording = true
  const isPhone = window.innerWidth <= 550
  const [stream, setStream] = useState();
  const [matches, setMatches] = useState([]);
  const [totalSongs, setTotalSongs] = useState(10);
  const [isListening, setisListening] = useState(false);
  const [audioInput, setAudioInput] = useState("device"); // or "mic"
  const [genFingerprint, setGenFingerprint] = useState(null);
  const [registeredMediaEncoder, setRegisteredMediaEncoder] = useState(false);

  const streamRef = useRef(stream);
  let sendRecordingRef = useRef(true);

  const ffmpegRef = useRef();

  useEffect(() => {
    streamRef.current = stream;
  }, [stream]);

  useEffect(() => {
    const ffmpeg = new FFmpeg();
    ffmpeg.load()
    ffmpegRef.current = ffmpeg
  }, [])

  useEffect(() => {
    if (isPhone) {
      setAudioInput("mic");
    }

    socket.on("connect", () => {
      socket.emit("totalSongs", "");
    });

    socket.on("matches", (matches) => {
      matches = JSON.parse(matches);
      if (matches) {
        setMatches(matches.slice(0, 5));
        console.log("Matches: ", matches);
      } else {
        toast("No song found.");
      }

      cleanUp();
    });

    socket.on("downloadStatus", (msg) => {
      msg = JSON.parse(msg);
      const msgTypes = ["info", "success", "error"];
      if (msg.type !== undefined && msgTypes.includes(msg.type)) {
        toast[msg.type](() => <div>{msg.message}</div>);
      } else {
        toast(msg.message);
      }
    });

    socket.on("totalSongs", (songsCount) => {
      setTotalSongs(songsCount);
    });
  }, []);

  useEffect(() => {
    const emitTotalSongs = () => {
      socket.emit("totalSongs", "");
    };

    const intervalId = setInterval(emitTotalSongs, 8000);

    return () => clearInterval(intervalId);
  }, []);

  useEffect(() => { 
    (async () => {
      try {
        const go = new window.Go();
        const result = await WebAssembly.instantiateStreaming(
          fetch(gowasm), 
          go.importObject
        );
        go.run(result.instance);

        if (typeof window.generateFingerprint === "function") {
          setGenFingerprint(() => window.generateFingerprint);
        }

      } catch (error) {
        setMatches([...matches, "Error loading WASM:", error.toString()])
        console.error("Error loading WASM:", error);
      }
    })();
  }, []);

  async function record() {
    const ffmpeg = ffmpegRef.current
    try {
      if (!genFingerprint) {
        setMatches([...matches, "WASM is not loaded yet."])
        console.error("WASM is not loaded yet.");
        return;
      }

      cleanUp();

      const inputFile = 'input.wav';
      const outputFile = 'output_mono.wav';

      let filePresent = false
      try {
        let fileData = await ffmpeg.readFile(outputFile)
        filePresent = fileData.length > 0
      }catch(ignored){}

      if(filePresent == 0) {
        await ffmpeg.writeFile(inputFile, await fetchFile(window.location.origin+"/Voilà.wav"))
        // Convert audio to mono with a sample rate of 44100 Hz
        const exitCode = await ffmpeg.exec([
          '-i', inputFile,
          '-c', 'pcm_s16le',
          '-ar', '44100',
          '-ac', '1',
          '-f', 'wav',
          outputFile
        ]);
        if (exitCode !== 0) {
          throw new Error(`FFmpeg exec failed with exit code: ${exitCode}`);
        }
      }

      const monoData = await ffmpeg.readFile(outputFile);
      const monoBlob = new Blob([monoData.buffer], { type: 'audio/wav' });

      const reader = new FileReader();
      reader.readAsArrayBuffer(monoBlob);
      reader.onload = async (event) => {
        const arrayBuffer = event.target.result;
        const audioContext = new AudioContext();
        const arrayBufferCopy = arrayBuffer.slice(0);
        const audioBufferDecoded = await audioContext.decodeAudioData(arrayBufferCopy);
        
        const audioData = audioBufferDecoded.getChannelData(0);
        const audioArray = Array.from(audioData);

        const result = genFingerprint(audioArray, audioBufferDecoded.sampleRate);
        if (result.error !== 0) {
          toast["error"](() => <div>An error occured</div>)
          console.log("An error occured: ", result)
          return
        }

        const fingerprintMap = result.data.reduce((dict, item, i) => {
          // if(i > 10) return dict
          dict[item.address] = item.anchorTime;
          return dict;
        }, {});
 
        // console.log("Fingerprint data: ")
        // console.log(JSON.stringify({ fingerprint: fingerprintMap }))
        // socket.compress(true).emit("newFingerprint", JSON.stringify({ fingerprint: fingerprintMap }));
        fetch(wsPlaceholder, {
          method: "POST",
          mode: 'cors',
          body: JSON.stringify({ fingerprint: fingerprintMap }),
          headers: {
            "Content-type": "application/json; charset=UTF-8"
          }
        }).then(r => {
          r.json().then(d => {
            setMatches(d.slice(0, 5));
          })
        }).catch(e => {
          setMatches([...matches, e.toString()])
        });

      };
    } catch (error) {
      console.error("error:", error);
      cleanUp();
    }
  }

  function downloadRecording(blob) {
    const blobUrl = URL.createObjectURL(blob);

    const downloadLink = document.createElement("a");
    downloadLink.href = blobUrl;
    downloadLink.download = "recorded_audio.wav";
    document.body.appendChild(downloadLink);
    downloadLink.click();
  }

  function cleanUp() {
    const currentStream = streamRef.current;
    if (currentStream) {
      currentStream.getTracks().forEach((track) => track.stop());
    }

    setMatches([])

    setStream(null);
    setisListening(false);
  }

  function stopListening() {
    cleanUp();
    sendRecordingRef.current = false;
  }

  function handleLaptopIconClick() {
    setAudioInput("device");
  }

  function handleMicrophoneIconClick() {
    setAudioInput("mic");
  }

  return (
    <div className="App">
      <div className="TopHeader">
        <h2 style={{ color: "#374151" }}>!Shazam -- LOFI</h2>
        <h4 style={{ display: "flex", justifyContent: "flex-end" }}>
          <AnimatedNumber includeComma={true} animateToNumber={totalSongs} />
          &nbsp;Songs
        </h4>
      </div>
      <div className="listen">
        <Listen
          stopListening={stopListening}
          disable={false}
          startListening={record}
          isListening={isListening}
        />
      </div>
      {!isPhone && (
        <div className="audio-input">
          <div
            onClick={handleLaptopIconClick}
            className={
              audioInput !== "device"
                ? "audio-input-device"
                : "audio-input-device active-audio-input"
            }
          >
            <LiaLaptopSolid style={{ height: 20, width: 20 }} />
          </div>
          <div
            onClick={handleMicrophoneIconClick}
            className={
              audioInput !== "mic"
                ? "audio-input-mic"
                : "audio-input-mic active-audio-input"
            }
          >
            <FaMicrophoneLines style={{ height: 20, width: 20 }} />
          </div>
        </div>
      )}
      <div className="youtube">
        {JSON.stringify(matches)}
        {/* <CarouselSliders matches={matches} /> */}
      </div>
      <Form socket={socket} toast={toast} />
      <ToastContainer
        position="top-center"
        autoClose={5000}
        hideProgressBar={true}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        pauseOnHover
        theme="light"
        transition={Slide}
      />
    </div>
  );
}

export default App;