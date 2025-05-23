# Import necessary libraries
import pandas as pd # For data manipulation and analysis
import matplotlib.pyplot as plt  # For plotting charts
import seaborn as sns # For data visualization
from sklearn.cluster import KMeans, DBSCAN # For K-Means Clustering and DBSCAN Clustering
from sklearn.preprocessing import StandardScaler # For feature scaling
from sklearn.decomposition import PCA # For Principal Component Analysis (dimensionality reduction)

# Load and preprocess the datasets
fast_food = ('fastfood.csv')
rec_intake = ('table-8-recommended-density-and-2017-2018-density.csv')

# Load the Recommended Food Intake Dataset here
intake_data = pd.read_csv(rec_intake)
intake_data.iloc[115:138]

# Load the Fast Food Dataset from Kaggle here
food_data = pd.read_csv(fast_food)
food_data.head()

# Outputs the number of Row and Column
food_data.shape

# Find null values of each column
null_values = dict(food_data.isnull().sum())
null_values

# Find percent null values
for i, n in null_values.items():
    print(f"null values for {i} = {(int(n)/food_data.shape[0])*100}%")

# Replace the null columns with mean values
null_cols = ['fiber','protein','vit_a','vit_c','calcium']
null_cols_avg = {}
for col in null_cols:
    null_cols_avg[col] = food_data[col].describe().mean()
null_cols_avg

# Drop non-needed data
food_data.drop(['salad','cal_fat','trans_fat'],axis=1,inplace=True)

# Fill in null values
food_data.fillna(value=null_cols_avg,inplace=True)
food_data.isnull().sum()

# Define recommended densities per 1000 kcal
recommended_density_per_1000cal = {
    'total_fat': 42.66,
    'sat_fat': 14.52,
    'sodium': 1747.65,
    'fiber': 5.95,
    'sugar': 5.69,
    'protein': 70.30,
    'calcium': 459.51
}

# Calculate per 1000 cal nutrient density
for nutrient in recommended_density_per_1000cal:
    col_name = f"{nutrient}_per_1000cal"
    food_data[col_name] = (food_data[nutrient] / food_data['calories']) * 1000

# Health scoring function
def compute_health_score(row):
    score = 0
    for nutrient, rec_value in recommended_density_per_1000cal.items():
        actual = row[f"{nutrient}_per_1000cal"]
        score += 1 / (abs(actual - rec_value) + 1)
    return score

food_data['health_score'] = food_data.apply(compute_health_score, axis=1)

min_score = food_data['health_score'].min()
max_score = food_data['health_score'].max()
food_data['Health Score'] = (food_data['health_score'] - min_score) / (max_score - min_score)

# Rule-based labeling
def classify_health(row):
    sodium = row['sodium_per_1000cal']
    fat = row['total_fat_per_1000cal']
    sugar = row['sugar_per_1000cal']
    sodium_limit = recommended_density_per_1000cal['sodium']
    fat_limit = recommended_density_per_1000cal['total_fat']
    sugar_limit = recommended_density_per_1000cal['sugar']

    if sodium <= sodium_limit and fat <= fat_limit:
        return 'Healthy'    # Healthy = low sodium and low fat
    elif (sodium > sodium_limit and fat <= fat_limit) or (fat > fat_limit and sodium <= sodium_limit):
        return 'Moderate'   # Moderate = low sodium and high fat or low fat and high sodium
    else:
        return 'Unhealthy'  # Unhealthy = high sodium and high fat

food_data['health_label'] = food_data.apply(classify_health, axis=1)

# Features and scaling
features = ['health_score', 'sodium_per_1000cal', 'total_fat_per_1000cal', 'sugar_per_1000cal']
X = food_data[features].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# KMeans clustering
kmeans = KMeans(n_clusters=2, random_state=42)
food_data['kmeans_cluster'] = kmeans.fit_predict(X_scaled)
centroids_scaled = kmeans.cluster_centers_
centroids = scaler.inverse_transform(centroids_scaled)

# DBSCAN clustering
dbscan = DBSCAN(eps=1.2, min_samples=5)
food_data['dbscan_cluster'] = dbscan.fit_predict(X_scaled)

# Reduce to 2D using PCA for visualization
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

# Save PCA coordinates for plotting
food_data['pca1'] = X_pca[:, 0]
food_data['pca2'] = X_pca[:, 1]

# Transform centroids too
centroids_pca = pca.transform(kmeans.cluster_centers_)

# Visualize KMeans clusters in PCA space
plt.figure(figsize=(10, 6))
sns.scatterplot(x='pca1', y='pca2', hue='kmeans_cluster', data=food_data, palette='Set2', s=80)
plt.scatter(centroids_pca[:, 0], centroids_pca[:, 1], color='red', s=200, marker='X', label='Centroids')
plt.title("KMeans Clustering (PCA Projection)")
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")
plt.grid(True)
plt.legend(title='Cluster')
plt.show()

# DBSCAN
plt.figure(figsize=(10, 6))
sns.scatterplot(x='pca1', y='pca2', hue='dbscan_cluster', data=food_data, palette='Dark2', s=80)
plt.title("DBSCAN Clustering")
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")
plt.grid(True)
plt.legend(title='DBSCAN Cluster')
plt.show()

# Rule-based health labels
plt.figure(figsize=(10, 6))
sns.scatterplot(x='pca1', y='pca2', hue='health_label', data=food_data, palette='coolwarm', s=80)
plt.title("Health Labels (Rule-Based)")
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")
plt.grid(True)
plt.legend(title='Health Label')
plt.show()

# List all the columns to display
columns_to_show = ['item', 'Health Score', 'calories', 'total_fat', 'sat_fat', 'sodium', 'fiber', 'sugar', 'protein', 'calcium']

# Round the food data by 5 decimal places
food_data = food_data.round(5)

# Print by score for each label
for label in ['Healthy', 'Moderate', 'Unhealthy']:
    print(f"\n--- {label} Meals ---")
    print(food_data[food_data['health_label'] == label][columns_to_show].sort_values(by='Health Score', ascending=False).to_string(index=False))
