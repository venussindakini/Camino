import os
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool

# ==========================================
# 0. 自動建立輸出 Folder 
# ==========================================
output_dir = "outputs_camino"
os.makedirs(output_dir, exist_ok=True)

my_llm = LLM(model="gemini/gemini-2.5-flash")
search_tool = SerperDevTool()

# ==========================================
# 1. 重新定義 4 大 Agents
# ==========================================

logistics_agent = Agent(
    role="路線與交通總監",
    goal="精準規劃 21 天行程。必須包含從香港(HKG)出發及回程的航班安排。每天步程嚴格控制在 7 公里以內，並提供點到點的交通方式與 Google Maps 連結。",
    backstory="你是地圖導航與航班規劃專家。你非常清楚每天從哪裡出發、到哪裡結束。你會生成精準的 Google Maps Directions URL 供用家隨時查看。",
    tools=[search_tool],
    llm=my_llm,
    max_iter=15, 
    verbose=True
)

local_guide_agent = Agent(
    role="食宿採購經理",
    goal="為每天的行程填補具體的：早餐、午餐、晚餐、以及住宿地點。重點推薦（如住宿和八爪魚餐廳）必須附上參考 URL。",
    backstory="你是當地的地頭蟲。每天到了目的地，你都知道哪裡有最好的八爪魚餐廳，哪裡有舒適安全的雙人房。",
    tools=[search_tool],
    llm=my_llm,
    max_iter=15, 
    verbose=True
)

budget_agent = Agent(
    role="財務與預算總監",
    goal="精確計算每人 1.5 萬港幣（總共 3 萬）預算內的各項開支，並列出【每人花費】與【總支出】的明細清單。",
    backstory="你是一位專業會計。你負責掌控預算，懂得計算香港來回機票、住宿、餐飲的預估開支，並整理成清晰的財務報表。",
    tools=[search_tool],
    llm=my_llm,
    max_iter=15,
    verbose=True
)

data_agent = Agent(
    role="數據處理與排版大師",
    goal="將所有路線、食宿、預算轉化為完美的格式：兩個英文版 CSV 表格，以及一份廣東話行程報告。",
    backstory="你是一位有強迫症的私人助理。你討厭廢話，喜歡一目了然的表格和精簡的排版。你絕不會漏掉任何重要的 URL。",
    llm=my_llm,
    verbose=True
)

# ==========================================
# 2. 重新定義 Tasks 
# ==========================================

plan_route = Task(
    description=(
        "為期 21 天的朝聖之旅（為了證書，走最後 100 多公里即可，例如 Sarria 起步）。"
        "⚠️ 重要新增：Day 1 必須是從香港 (HKG) 出發飛往西班牙的交通日。Day 21 必須是從西班牙出發飛返香港 (HKG) 的交通日。"
        "嚴格限制：每天徒步距離 < 7 公里。如果走完 100km 還剩很多天，安排在 Santiago 深度遊。"
        "列出每天的：Day X, 起點, 終點, 距離, 交通方式(Flight/Walk/Bus), 以及 Google Maps 路線連結。"
    ),
    expected_output="21天每日路線表，包含香港來回航班安排。",
    agent=logistics_agent
)

plan_food_and_hotel = Task(
    description=(
        "根據路線總監的每日目的地，安排每天的：早餐、午餐、晚餐、住宿。"
        "⚠️ 減壓指令：普通的早晚餐你可以依靠內部知識推薦即可。但是，【每天的住宿地點】以及【Melide的正宗加利西亞八爪魚餐廳】這兩項，【必須】上網搜尋並提供真實的網址 URL。"
    ),
    expected_output="21天完整的食宿配對表，住宿與重點餐廳附帶 URL。",
    agent=local_guide_agent
)

plan_budget = Task(
    description=(
        "根據前兩項任務的航班及食宿安排，估算所有的開支（包括機票、21天食宿、當地交通等）。"
        "⚠️ 預算要求：必須清楚列明【每人開支 (Cost Per Person)】以及【兩人總支出 (Total Cost)】。總預算控制在 $30,000 HKD 內。"
    ),
    expected_output="詳細的開支估算清單，區分每人與總花費。",
    agent=budget_agent
)

export_itinerary_csv = Task(
    description=(
        "將行程資料生成為第一個 CSV 檔案。為了避免亂碼，必須【全英文 (ALL ENGLISH)】填寫。"
        "CRITICAL FORMATTING RULES: "
        "1. 所有欄位必須用雙引號 \" \" 包圍。"
        "2. URL 必須使用 Excel 公式: \"=HYPERLINK(\"\"URL\"\", \"\"Click Here\"\")\""
        "3. 欄位必須是: \"Day\", \"From_To\", \"Distance\", \"Transport\", \"Breakfast\", \"Lunch\", \"Dinner\", \"Accommodation\", \"Map_Route\", \"Reference_URLs\""
    ),
    expected_output="完美的 21 行 CSV 行程表 (全英文)。",
    agent=data_agent,
    output_file=f"{output_dir}/camino_daily_itinerary.csv" 
)

export_budget_csv = Task(
    description=(
        "將財務總監的預算資料生成為第二個 CSV 檔案。必須【全英文 (ALL ENGLISH)】填寫。"
        "CRITICAL FORMATTING RULES: "
        "1. 所有欄位必須用雙引號 \" \" 包圍。"
        "2. 欄位必須是: \"Category\", \"Description\", \"Cost_Per_Person_HKD\", \"Total_Cost_HKD\""
    ),
    expected_output="預算明細 CSV 表格 (全英文)。",
    agent=data_agent,
    output_file=f"{output_dir}/camino_budget_summary.csv" 
)

write_report = Task(
    description=(
        "將所有資料寫成一篇【廣東話（繁體中文）】的行程書。"
        "排版要求："
        "1. 內容長度需大約相當於 5 頁 A4 紙（約 2000 字），不可過度冗長，必須精簡扼要。"
        "2. 每日行程必須一目了然（含香港出發及回程），列明交通、三餐、住宿，並將所有地圖和食宿的 URL 用 Markdown 格式 [地點名稱](URL) 嵌入。"
        "3. 必須加入一個段落，詳細列出【每人花費】與【總支出】的預算表。"
        "4. 加入如何領取證書的步驟。"
    ),
    expected_output="約 5 頁紙長度的精簡廣東話 Markdown 行程報告，包含所有連結與預算表。",
    agent=data_agent,
    output_file=f"{output_dir}/camino_5pages_report.md" 
)

# ==========================================
# 3. START THE CREW
# ==========================================

travel_crew = Crew(
    agents=[logistics_agent, local_guide_agent, budget_agent, data_agent],
    tasks=[plan_route, plan_food_and_hotel, plan_budget, export_itinerary_csv, export_budget_csv, write_report],
    process=Process.sequential 
)

print("正在啟動【完美出行版】朝聖規劃團隊 (含香港來回航班、獨立預算 Excel)...")
print("這是一個非常龐大的運算，請耐心等候約 3-4 分鐘...")

result = travel_crew.kickoff(inputs={})

print("\n================================================")
print("大功告成！請打開 outputs_camino 資料夾檢查：")
print("1. camino_daily_itinerary.csv (每日行程與地圖)")
print("2. camino_budget_summary.csv (每人與總開支預算表)")
print("3. camino_5pages_report.md (廣東話終極報告)")
print("================================================")