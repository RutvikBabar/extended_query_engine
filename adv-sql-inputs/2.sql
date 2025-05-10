SELECT 
    prod,
    month,
    AVG(CASE WHEN s1.month < s.month AND s1.prod = s.prod THEN s1.quant ELSE NULL END) AS avg_1_quant,
    AVG(CASE WHEN s2.month > s.month AND s2.prod = s.prod THEN s2.quant ELSE NULL END) AS avg_2_quant
FROM 
    sales s
CROSS JOIN 
    sales s1
CROSS JOIN 
    sales s2
GROUP BY 
    s.prod, s.month
