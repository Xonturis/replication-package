SELECT 
    gm.rel_time - MIN(gm.rel_time) OVER (PARTITION BY gm.test_id ORDER BY gm.rel_time) AS relative_rel_time,
    gm.{metric}, 
    SUM({metric}) OVER (ORDER BY rel_time ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumul,
    gm.test_id 
FROM GSPT_Measure gm
WHERE gm.test_id = {test}
AND gm.{metric} NOT NULL
ORDER BY gm.rel_time ASC;
