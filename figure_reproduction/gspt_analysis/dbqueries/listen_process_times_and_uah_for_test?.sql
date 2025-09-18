WITH
  baseline AS (
    SELECT
      MIN(rel_time) AS min_time
    FROM
      GSPT_Measure
    WHERE
      test_id = {test}
  ),
  process_times AS (
    SELECT
      MIN(gm.rel_time) + 5 - b.min_time AS start_process_relative_rel_time,
      MAX(gm.rel_time) - 10 - b.min_time AS end_process_relative_rel_time,
      gm.step_id,
      gs.name,
      gm.test_id,
      b.min_time
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
      b.min_time
  )
SELECT
  SUM(gm.AH_PL)/1000,
  start_process_relative_rel_time,
  end_process_relative_rel_time,
  gm.step_id,
  pt.name,
  gm.test_id
FROM
  process_times pt
  JOIN GSPT_Measure gm ON gm.test_id = pt.test_id
WHERE
  (gm.rel_time - pt.min_time) BETWEEN pt.start_process_relative_rel_time AND pt.end_process_relative_rel_time
GROUP BY
  gm.step_id,
  pt.name,
  gm.test_id,
  pt.min_time,
  pt.start_process_relative_rel_time,
  pt.end_process_relative_rel_time;