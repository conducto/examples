import pandas
import sys

df = pandas.read_csv(sys.argv[1])

print("Stats on 100 largest US cities")
print()
print(f"Total population: {df.population.sum()}")
print()
print(f"Population by state:\n{df.groupby('state').population.sum()}")