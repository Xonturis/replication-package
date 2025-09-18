WITH baseline AS (
    SELECT MIN(rel_time) AS min_time 
    FROM GSPT_Measure 
    WHERE test_id = {test}
),
times AS (
SELECT 
    MIN(gm.rel_time) - b.min_time + 5  AS start_process_relative_rel_time,
    MAX(gm.rel_time) - b.min_time - 10 AS end_process_relative_rel_time
FROM GSPT_Measure gm
JOIN GSPT_Step gs
ON gs.id = gm.step_id
CROSS JOIN baseline b
WHERE gm.test_id = {test}
AND gs.name LIKE '%Listen'
AND gm.{metric} NOT NULL
GROUP BY gm.step_id, gs.name, gm.test_id, b.min_time
)
SELECT
	rel_time - b.min_time AS relative_rel_time, 
	COALESCE(
		(
			SELECT 1
			FROM times t
			WHERE 
				(gm.rel_time - b.min_time) BETWEEN t.start_process_relative_rel_time AND end_process_relative_rel_time
		) * gm.{metric},
		0
	) AS {metric},
	gs.name
FROM GSPT_Measure gm
JOIN GSPT_Step gs
ON gs.id = gm.step_id
CROSS JOIN baseline b
WHERE gm.test_id = {test}
;