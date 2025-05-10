WITH yearly_avg AS (
    SELECT 
        year,
        AVG(quant) AS avg_quant
    FROM 
        sales
    GROUP BY 
        year
)
SELECT 
    s.prod,
    s.year,
    s.month,
    monthly_filtered.sum_quant AS sum_2_quant,
    yearly_sum.sum_quant AS sum_3_quant,
    ya.avg_quant AS avg_1_quant
FROM 
    (SELECT DISTINCT prod, year, month FROM sales) s
JOIN 
    yearly_avg ya 
ON 
    s.year = ya.year
LEFT JOIN 
    (SELECT 
        s1.prod, s1.year, s1.month,
        SUM(s1.quant) AS sum_quant
     FROM 
        sales s1
     JOIN 
        yearly_avg ya 
     ON 
        s1.year = ya.year
     WHERE 
        s1.quant > ya.avg_quant
     GROUP BY 
        s1.prod, s1.year, s1.month) monthly_filtered
ON 
    s.prod = monthly_filtered.prod AND 
    s.year = monthly_filtered.year AND 
    s.month = monthly_filtered.month
LEFT JOIN 
    (SELECT 
        s2.prod, s2.year,
        SUM(s2.quant) AS sum_quant
     FROM 
        sales s2
     GROUP BY 
        s2.prod, s2.year) yearly_sum
ON 
    s.prod = yearly_sum.prod AND 
    s.year = yearly_sum.year
