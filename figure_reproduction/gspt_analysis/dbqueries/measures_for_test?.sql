SELECT 
    gm.rel_time,
    gm.rel_time - MIN(gm.rel_time) OVER (PARTITION BY gm.test_id ORDER BY gm.rel_time) AS relative_rel_time,
    gm.AH_PL, 
    gm.C_ID, 
    gm.C_PL, 
    gm.D_ID, 
    gm.D_IN_ID, 
    gm.D_OUT_ID, 
    gm.M_ID, 
    gm.M_PL, 
    gm.O_DPacket_ID,
    gm.test_id 
FROM GSPT_Measure gm
WHERE gm.test_id = {test}
ORDER BY gm.rel_time ASC;