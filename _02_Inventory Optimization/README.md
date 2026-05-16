

### Objective:

Design an intelligent system to **maintain optimal inventory levels**, reducing both stockouts (lost sales) and overstock (waste and storage costs). The system will learn from demand trends and product turnover rates.

---

###  Key Features Used:

- **Inventory Level** (starting daily stock)
    
- **Units Sold**, **Demand Forecast**
    
- **Lead time** (assumed or provided per product)
    
- **Promotion/Holiday Flags**
    
- **Category**, **Product ID**, **Store ID**
    
- Forecasted demand (from Challenge 1)
    

---

###  Methodologies:

1. **Descriptive Analytics:**
    
    - Analyze stockout frequency, shelf life, overstocks
        
2. **Traditional Inventory Models:**
    
    - EOQ (Economic Order Quantity)
        
    - Reorder Point & Safety Stock models
        
3. **Optimization Algorithms:**
    
    - Linear Programming for multi-SKU restocking
        
    - Simulations using (s, S) or (Q, R) policies
        
4. **Machine Learning/AI:**
    
    - Predict optimal reorder quantity using regression
        
    - Classify stock risk zones (e.g., “High Stockout Risk”)
        
5. **Reinforcement Learning (Advanced):**

	- **Agent-Environment Setup:**
    
	    - The environment simulates store operations (daily sales, deliveries, and holding costs).
        
	    - The agent decides when and how much to reorder.
        
	- **States:** Current inventory, forecasted demand, days left in cycle, promotion status.
    
	- **Actions:** Reorder quantity (discrete or continuous).
    
	- **Rewards:** Negative of total cost (ordering + holding + stockout penalties).
    
	- **Algorithms:** Q-learning, Deep Q-Network (DQN), or Policy Gradient Methods.
    
	- Helps uncover non-obvious reorder policies that adapt to demand variability.
    

---

###  **Evaluation Metrics:**

To assess the effectiveness of the optimization strategy:

- **Stockout Rate:** % of days with unmet demand.
    
- **Service Level:** % of total demand fulfilled without delay.
    
- **Inventory Turnover Ratio:** Frequency at which stock is sold and replaced.
    
- **Holding Cost:** Cost of unsold inventory per day.
    
- **Ordering Cost:** Total cost incurred from placing orders.
    
- **Total Supply Chain Cost:** Combined cost of holding, stockouts, and reordering.
    

---

### **Expected Deliverables:**

- **Inventory Policy Recommender:**
    
    - For each product-store combination, a recommended policy (e.g., reorder at 20 units, restock 80 units).
        
- **Restocking Simulation Tool:**
    
    - Simulate different stocking strategies across scenarios (peak season, promotions, etc.).
        
- **Dashboard:**
    
    - Visualize stockout risks, inventory heatmaps, and cost breakdowns.
        
- **Alerts:**
    
    - Predictive warnings for potential stockout or overstock zones.
        

---

### **Business Impact:**

By adopting data-driven inventory policies:

- Reduce capital tied up in unsold stock
    
- Improve availability of high-demand products
    
- Enable faster response to demand surges (e.g., holidays, regional events)
    
- Optimize logistics by consolidating smarter reorder cycles