SELECT *
FROM GSPT_Environment ge
WHERE ge.id IN (
    SELECT gt.env_id
    FROM GSPT_Test gt
    WHERE gt.id = {test}
)