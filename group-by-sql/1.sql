SELECT 
    main.cust,
    ny.sum_quant AS sum_1_quant,
    ny.avg_quant AS avg_1_quant,
    ny.max_quant AS max_1_quant,
    ny.min_quant AS min_1_quant,
    ny.count_quant AS count_1_quant,
    ct.sum_quant AS sum_2_quant,
    ct.avg_quant AS avg_2_quant,
    ct.max_quant AS max_2_quant,
    ct.min_quant AS min_2_quant,
    ct.count_quant AS count_2_quant
FROM 
    (SELECT DISTINCT cust FROM sales) main
LEFT JOIN 
    (SELECT 
        cust,
        SUM(quant) AS sum_quant,
        AVG(quant) AS avg_quant,
        MAX(quant) AS max_quant,
        MIN(quant) AS min_quant,
        COUNT(quant) AS count_quant
     FROM sales
     WHERE state = 'NY'
     GROUP BY cust) ny ON main.cust = ny.cust
LEFT JOIN 
    (SELECT 
        cust,
        SUM(quant) AS sum_quant,
        AVG(quant) AS avg_quant,
        MAX(quant) AS max_quant,
        MIN(quant) AS min_quant,
        COUNT(quant) AS count_quant
     FROM sales
     WHERE state = 'CT'
     GROUP BY cust) ct ON main.cust = ct.cust
