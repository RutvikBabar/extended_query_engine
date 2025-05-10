SELECT 
    main.prod,
    main.month,
    before_month.avg_quant AS avg_1_quant,
    after_month.avg_quant AS avg_2_quant
FROM 
    (SELECT DISTINCT prod, month FROM sales) main
LEFT JOIN 
    (SELECT 
        s1.prod,
        s1.month AS main_month,
        AVG(s2.quant) AS avg_quant
     FROM 
        (SELECT DISTINCT prod, month FROM sales) s1
     JOIN 
        sales s2 ON s1.prod = s2.prod AND s2.month < s1.month
     GROUP BY 
        s1.prod, s1.month) before_month 
    ON main.prod = before_month.prod AND main.month = before_month.main_month
LEFT JOIN 
    (SELECT 
        s1.prod,
        s1.month AS main_month,
        AVG(s2.quant) AS avg_quant
     FROM 
        (SELECT DISTINCT prod, month FROM sales) s1
     JOIN 
        sales s2 ON s1.prod = s2.prod AND s2.month > s1.month
     GROUP BY 
        s1.prod, s1.month) after_month 
    ON main.prod = after_month.prod AND main.month = after_month.main_month
