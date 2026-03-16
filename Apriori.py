import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules

# 假设 df 是包含交易数据的 DataFrame，数据格式已经转换为适合的格式
df = pd.read_csv('transactions.csv')

# 生成频繁项集
frequent_itemsets = apriori(df, min_support=0.01, use_colnames=True)

# 生成关联规则
rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1)

# 输出推荐规则
print(rules)