SELECT 
    cust,
    SUM(CASE WHEN state = 'NY' THEN quant ELSE 0 END) AS sum_1_quant,
    AVG(CASE WHEN state = 'NY' THEN quant ELSE NULL END) AS avg_1_quant,
    MAX(CASE WHEN state = 'NY' THEN quant ELSE NULL END) AS max_1_quant,
    MIN(CASE WHEN state = 'NY' THEN quant ELSE NULL END) AS min_1_quant,
    COUNT(CASE WHEN state = 'NY' THEN quant ELSE NULL END) AS count_1_quant,
    SUM(CASE WHEN state = 'CT' THEN quant ELSE 0 END) AS sum_2_quant,
    AVG(CASE WHEN state = 'CT' THEN quant ELSE NULL END) AS avg_2_quant,
    MAX(CASE WHEN state = 'CT' THEN quant ELSE NULL END) AS max_2_quant,
    MIN(CASE WHEN state = 'CT' THEN quant ELSE NULL END) AS min_2_quant,
    COUNT(CASE WHEN state = 'CT' THEN quant ELSE NULL END) AS count_2_quant
FROM sales
GROUP BY cust
