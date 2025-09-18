WITH
  baseline AS (
    SELECT
      MIN(rel_time) AS min_time
    FROM
      GSPT_Measure
    WHERE
      test_id = {test}
  )
SELECT
  MIN(gm.rel_time) + 5 - b.min_time AS start_process_relative_rel_time,
  MAX(gm.rel_time) - 10 - b.min_time AS end_process_relative_rel_time,
  gm.step_id,
  gs.name,
  gm.test_id
FROM
  GSPT_Measure gm
  JOIN GSPT_Step gs ON gs.id = gm.step_id
  CROSS JOIN baseline b
WHERE
  gm.test_id = {test}
  AND gs.name LIKE '%Listen'
GROUP BY
  gm.step_id,
  gs.name,
  gm.test_id,
  b.min_time;