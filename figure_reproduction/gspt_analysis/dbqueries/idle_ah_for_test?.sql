SELECT SUM(gm.AH_PL) AS AH_PL, MAX(gm.rel_time) - MIN(gm.rel_time) AS duration
FROM GSPT_Measure gm
WHERE gm.test_id = {test}
AND gm.step_id = (SELECT id FROM GSPT_Step where name = 'PAUSE_referenceST')
GROUP BY gm.step_id