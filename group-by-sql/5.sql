SELECT 
    main.cust,
    main.prod,
    self_avg.avg_quant AS avg_1_quant,
    others_avg.avg_quant AS avg_2_quant
FROM 
    (SELECT DISTINCT cust, prod FROM sales) main
JOIN 
    (SELECT 
        cust, prod,
        AVG(quant) AS avg_quant
     FROM 
        sales
     GROUP BY 
        cust, prod) self_avg
ON 
    main.cust = self_avg.cust AND 
    main.prod = self_avg.prod
JOIN 
    (SELECT 
        s1.prod,
        s1.cust,
        AVG(s2.quant) AS avg_quant
     FROM 
        (SELECT DISTINCT prod, cust FROM sales) s1
     JOIN 
        sales s2
     ON 
        s1.prod = s2.prod AND 
        s1.cust != s2.cust
     GROUP BY 
        s1.prod, s1.cust) others_avg
ON 
    main.cust = others_avg.cust AND 
    main.prod = others_avg.prod
WHERE 
    others_avg.avg_quant > self_avg.avg_quant
