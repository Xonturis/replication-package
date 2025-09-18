WITH baseline AS (
    SELECT MIN(rel_time) AS min_time 
    FROM GSPT_Measure 
    WHERE test_id = {test}
)
SELECT {aggr}(gm.{metric}) AS aggr, MIN(gm.rel_time) - b.min_time AS start, MAX(gm.rel_time) - b.min_time AS end, gs.name
FROM GSPT_Measure gm
JOIN GSPT_Step gs
ON gs.id = gm.step_id
CROSS JOIN baseline b
WHERE 
gm.test_id = {test}
AND (gs.name LIKE '%Listen' AND gs.name NOT LIKE '%\_%' ESCAPE '\' AND gs.name NOT LIKE 'first%')
GROUP BY gs.name, b.min_time;