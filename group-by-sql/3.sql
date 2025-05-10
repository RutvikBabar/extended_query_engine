SELECT 
    ny.cust,
    ny.sum_1_quant,
    ny.avg_1_quant,
    ny.max_1_quant,
    ny.min_1_quant,
    ny.count_1_quant,
    ct.sum_2_quant,
    ct.avg_2_quant,
    ct.max_2_quant,
    ct.min_2_quant,
    ct.count_2_quant
FROM 
    (SELECT 
        cust,
        SUM(quant) AS sum_1_quant,
        AVG(quant) AS avg_1_quant,
        MAX(quant) AS max_1_quant,
        MIN(quant) AS min_1_quant,
        COUNT(quant) AS count_1_quant
     FROM 
        sales
     WHERE 
        state = 'NY'
     GROUP BY 
        cust) ny
FULL OUTER JOIN 
    (SELECT 
        cust,
        SUM(quant) AS sum_2_quant,
        AVG(quant) AS avg_2_quant,
        MAX(quant) AS max_2_quant,
        MIN(quant) AS min_2_quant,
        COUNT(quant) AS count_2_quant
     FROM 
        sales
     WHERE 
        state = 'CT'
     GROUP BY 
        cust) ct
ON ny.cust = ct.cust
