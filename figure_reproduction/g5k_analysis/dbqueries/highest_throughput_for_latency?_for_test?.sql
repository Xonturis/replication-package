SELECT *
FROM G5K_Throughput_Measure gm
WHERE gm.test_id = {test}
AND gm.nnth_response_time <= {latency}
ORDER BY gm.throughput DESC
LIMIT 1