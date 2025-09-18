WITH baseline AS (
    SELECT MIN(rel_time) AS min_time 
    FROM GSPT_Measure 
    WHERE test_id = {test}
)
SELECT 
    MIN(gm.rel_time) - b.min_time AS relative_rel_time,
    gm.step_id,
    gs.name
FROM GSPT_Measure gm
JOIN GSPT_Step gs
ON gs.id = gm.step_id
CROSS JOIN baseline b
WHERE gm.test_id = {test}
GROUP BY gm.step_id, gs.name, b.min_time;