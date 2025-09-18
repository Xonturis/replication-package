SELECT {aggreg}, gs.name, gt.network, ge.device, ge.OS, ge.platform, ge.version FROM GSPT_Measure gm
JOIN GSPT_Step gs 
ON gs.id = gm.step_id 
JOIN GSPT_Test gt 
ON gm.test_id = gt.id 
LEFT JOIN GSPT_Environment ge
ON ge.id = gt.env_id
GROUP BY CUBE(gs.name, gt.network, ge.device, ge.OS, ge.platform, ge.version);