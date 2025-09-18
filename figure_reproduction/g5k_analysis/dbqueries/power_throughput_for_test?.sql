SELECT t.throughput, MEDIAN(p.power) AS power
FROM G5K_Throughput_Measure t
JOIN (
	SELECT MEDIAN(p.power) AS power, FLOOR(p.rel_time) AS ptime 
	FROM G5K_Power_Measure p
	WHERE p.test_id = t.test_id
	GROUP BY ptime
) p ON FLOOR(t.rel_time) = p.ptime
WHERE t.test_id = {test}
GROUP BY t.throughput