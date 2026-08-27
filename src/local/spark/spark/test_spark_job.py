from pyspark.sql import SparkSession
from commons.utils import load_df

spark = SparkSession.builder.appName("SparkJob").getOrCreate()
df = load_df(spark, "../data/test.csv", "csv")
print(df.show(5))
