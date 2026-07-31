import asyncio
import streamlit as st

from scraper.telegram_client import TelegramClientManager
from scraper.channel_search import TelegramSearch
from scraper.access import AccessManager
from scraper.message_scraper import MessageScraper
from scraper.channel_analyzer import ChannelAnalyzer
from scraper.investigation_scorer import ChannelScorer
from scraper.utils.csv_exporter import CSVExporter

async def check_private_channels(channels):

    manager = TelegramClientManager()
    client = await manager.connect()

    access = AccessManager(client)

    results = {}

    for channel in channels:

        results[channel.id] = await access.check_access(channel)

    await manager.disconnect()

    return results


async def search(keyword):

    manager = TelegramClientManager()
    client = await manager.connect()

    search_engine = TelegramSearch(client)

    channels = await search_engine.search_channels(keyword)

    await manager.disconnect()

    return channels

    



#Analyze selected channels and score them
async def analyze_selected_channels(selected_channels,weights):

    manager = TelegramClientManager()
    client = await manager.connect()

    access_manager = AccessManager(client)
    analyzer = ChannelAnalyzer(client)
    scorer = ChannelScorer(weights)

    results = []

    for channel in selected_channels:

        access = await access_manager.check_access(channel)

        if access["entity"] is None:
            continue

        report = await analyzer.analyze_channel(
            access["entity"],limit=5000
        )

        score = scorer.score_channel(report)

        results.append({
            "channel": channel,
            "report": report,
            "score": score
        })

    await manager.disconnect()
    return results


# Scrape selected channels and download messages
async def scrape_selected_channels(selected_channels,weights):

    manager = TelegramClientManager()
    client = await manager.connect()

    access_manager = AccessManager(client)
    scraper = MessageScraper(client)

    analyzer = ChannelAnalyzer(client)
    scorer = ChannelScorer(weights)

    exporter = CSVExporter()

    results = []

    for channel in selected_channels:

        access = await access_manager.check_access(channel)

        if access["entity"] is None:
            continue

        # Download media (QR images are kept)
        messages = await scraper.scrape_messages(
            access["entity"],
            channel.title,
            limit=500
        )

        # Analyze channel messages
        report = await analyzer.analyze_channel(
            access["entity"],
            limit=500
        )

        # Extract wallet / UPI information
        score = scorer.score_channel(report)

        # Export wallet report
        csv_path = exporter.export_messages(
            channel.title,
            score["wallet_report"]      # <-- this will be added in investigation_scorer.py
        )

        results.append({

            "channel": channel.title,
            "csv_path": csv_path,
            "message_count": len(score["wallet_report"])

        })

    await manager.disconnect()
    return results



# Streamlit UI
st.set_page_config(
    page_title="Telegram Investigation Tool",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Telegram Investigation Tool")


# Session State
if "channels" not in st.session_state:
    st.session_state.channels = []

if "results" not in st.session_state:
    st.session_state.results = []


# Search Section

profile = st.selectbox("Investigation Profile",
        ["Custom","Crypto","Crypto + Drugs","Money Laundering","Terror Financing"])


st.markdown("### 🎯 Investigation Scoring")

drug_weight = st.slider("💊 Drugs", 0, 10, 0)
crypto_weight = st.slider("₿ Crypto", 0, 10, 0)
terror_weight = st.slider("🚨 Terror Financing", 0, 10, 0)
fraud_weight = st.slider("💳 Fraud", 0, 10, 0)
money_weight = st.slider("💰 Money Laundering", 0, 10, 0)
india_weight = st.slider("🇮🇳 India Indicators", 0, 10, 0)


weights = {
    "drug": drug_weight,
    "crypto": crypto_weight,
    "terror": terror_weight,
    "fraud": fraud_weight,
    "money": money_weight,
    "india": india_weight}

# if profile != "Custom":
#     st.info(f"Using predefined keywords for: {profile}")
if profile == "Crypto":
    st.info(
        "Query: crypto OR bitcoin OR btc OR usdt OR eth OR wallet"
    )

elif profile == "Crypto + Drugs":
    st.info(
        "Query: crypto OR wallet OR usdt OR btc OR p2p OR otc OR escrow OR drug OR drugs OR weed OR cocaine OR meth"
    )

elif profile == "Money Laundering":
    st.info(
        "Query: hawala OR laundering OR money laundering OR launder money OR laundering service OR illicit funds OR black money OR cash conversion"
    )

elif profile == "Terror Financing":
    st.info(
        "Query: terrorist financing OR terror funding OR crypto donation OR anonymous donation OR hawala OR sanctions evasion OR money mule"
    )

# keyword = st.text_input(
#     "Enter Keywords (comma separated)",
#     placeholder="Example: crypto, wallet, usdt, p2p"
# )

keyword = st.text_input(
    "Boolean Search Query",
    placeholder="""Examples:
    (drugs OR crypto) AND delhi 
    (wallet OR usdt) AND india 
    terror AND (crypto OR donation)

"""
)

if st.button("Search"):

    if profile == "Crypto":

        keyword = "crypto OR bitcoin OR btc OR usdt OR eth OR wallet"

    elif profile == "Crypto + Drugs":

        keyword = ("crypto OR wallet OR usdt OR btc OR p2p OR otc OR escrow ""OR drug OR drugs OR weed OR cocaine OR meth"
)


    elif profile == "Money Laundering":

        keyword = (
        "hawala OR laundering OR wallet OR usdt OR p2p OR otc OR transfer"
)

    elif profile == "Terror Financing":

        keyword = (
            "crypto OR wallet OR usdt OR btc OR donation OR funding"
)

    if keyword.strip() == "":
        st.warning("Please enter a keyword.")
        st.stop()

    with st.spinner("Searching Telegram..."):

        st.session_state.channels = asyncio.run(search(keyword))

        st.session_state.results = []

    if not st.session_state.channels:
        st.error("❌ No channels found for this keyword.")
        st.stop()



# Display Search Results
if st.session_state.channels:

    st.success(f"{len(st.session_state.channels)} channels found.")

    st.divider()

    st.subheader("Search Results")

    selected_channels = []

    public_channels = [
        c for c in st.session_state.channels
        if c.public]

    private_channels = [
        c for c in st.session_state.channels
        if not c.public]
    
    with st.expander(f"🌍 Public Channels ({len(public_channels)})", expanded=True):

        # Select All checkbox

        select_all_public = st.checkbox("Select All Public Channels",key="select_all_public")
        for channel in public_channels:

            with st.container(border=True):

                col1, col2 = st.columns([1,12])

                with col1:
                    if select_all_public:
                        selected = True
                        st.checkbox( "",value=True,disabled=True,key=f"channel_{channel.id}")
                    else:
                        selected = st.checkbox("",key=f"channel_{channel.id}")

                with col2:
                    st.markdown(f"### {channel.title}")
                    st.write(f"Username : {channel.username}")
                    st.write(f"Type : {channel.type}")

                if selected:
                    selected_channels.append(channel)

    
    private_selected = []

    with st.expander(f"🔒 Private Channels ({len(private_channels)})",expanded=True):
        if len(private_channels) == 0:

            st.info("No private channels found.")

        else:
            with st.spinner("Checking access for private channels..."):

                private_results = asyncio.run(
                    check_private_channels(private_channels)
                )
            for channel in private_channels:

                with st.container(border=True):

                    col1, col2 = st.columns([1, 12])

                    with col1:

                        selected = st.checkbox("",
                        key=f"private_{channel.id}"
                        )

                    with col2:

                        st.markdown(f"### {channel.title}")
                        st.write(f"Type : {channel.type}")

                    if selected:
                        private_selected.append(channel)

                    result = private_results[channel.id]

                    if result["status"] == "accessible":

                        st.success("✅ Accessible")
                        st.info("Ready for Analysis and Scraping.")

                    elif result["status"] == "join_required":

                        st.warning("🔒 Join Required")
                        st.info(
                            "Join manually using Telegram.\n"
                            "After joining, click Search again."
                )

                    elif result["status"] == "restricted":

                        st.error("🚫 Access Restricted")
                        st.info("Unable to access this private channel.")

    st.divider()

    all_selected = selected_channels + private_selected
    if st.button("Analyze all Selected Channels"):

        if not all_selected:

            st.warning("Please select at least one channel.")

        else:

            with st.spinner("Analyzing channels"):

                st.session_state.results = asyncio.run(
                    analyze_selected_channels(all_selected,weights)
                )
                st.session_state.results = sorted(
                    st.session_state.results,
                    key=lambda x: x["score"]["score"],
                    reverse=True
                )



# Display Analysis Results
if st.session_state.results:

    st.divider()
    st.header("🏆 Investigation Ranking")
    high = sum(1 for r in st.session_state.results
        if r["score"]["score"] >= 80
    )

    medium = sum(1 for r in st.session_state.results
        if 50 <= r["score"]["score"] < 80
    )
    low = sum(1 for r in st.session_state.results
        if r["score"]["score"] < 50
    )   

    col1, col2, col3 = st.columns(3)

    col1.metric("⭐ Highly Relevant", high)
    col2.metric("🟡 Relevant", medium)
    col3.metric("🔴 Low Priority", low)

    scrape_channels = []

    for rank, result in enumerate(st.session_state.results, start=1):

        report = result["report"]
        score = result["score"]

        rank_icon = ("🥇" if rank == 1 else"🥈" if rank == 2 else"🥉" if rank == 3 else"📌")

        with st.expander(
            f"{rank_icon} Rank {rank} : {report['title']} ({score['score']}/100)",
            expanded=False):

            col1, col2 = st.columns([1, 12])

            with col1:

                scrape = st.checkbox(
                    "",
                    key=f"scrape_{report['id']}"
                )

            

            if scrape:
                scrape_channels.append(result["channel"])

            # Score Display

            if score["score"] >= 80:

                st.success(
                    f"⭐ Highly Relevant ({score['score']}/100)"
                )

            elif score["score"] >= 50:

                st.warning(
                    f"🟡 Relevant ({score['score']}/100)"
                )

            else:

                st.error(
                    f"🔴 Low Priority ({score['score']}/100)"
                )

            st.write(f"**Recommendation:** {score['recommendation']}")
            st.write(f"Raw Score : {score['raw_score']}")
            st.write(f"Normalized Score : {score['score']}/100")

            st.write(f"Participants : {report['participants']}")

            st.write(f"Description : {report['description']}")

            st.write(f"Recent Messages : {report['total_messages']}")

            st.write(f"Text Messages : {report['text_messages']}")

            st.write(f"Media Messages : {report['media_messages']}")

            st.write(
                f"Average Views : {report['average_views']:.2f}"
            )

            st.write(
                f"Average Forwards : {report['average_forwards']:.2f}"
            )

            st.write("### Investigation Indicators")

            st.write(
                f"🪙 Crypto Indicators : {score['crypto_keyword_count']}"
            )

            st.write(
                f"💰 Financial Indicators : {score['financial_keyword_count']}"
            )

            st.write(
                f"💊 Drug Indicators : {score['drug_keyword_count']}"
            )

            st.write(
                f"🚨 Fraud Indicators : {score['fraud_keyword_count']}"
            )

            st.write(
                f"🔗 URLs : {score['url_count']}"
            )

            st.write(
                f"👛 Wallet Addresses : {score['wallet_addresses']}"
            )

            st.write(
                f"📨 Telegram Mentions : {score['telegram_mentions']}"
            )

            st.write(
                f"#️⃣ Hashtags : {score['hashtags']}"
            )
            st.write("### Matched Keywords")

            if score["matched_crypto"]:
                st.write("🪙 Crypto")
                st.write(", ".join(score["matched_crypto"]))

            if score["matched_financial"]:
                st.write("💰 Financial")
                st.write(", ".join(score["matched_financial"]))
            
            if score["matched_drugs"]:
                st.write("💊 Drugs")
                st.write(", ".join(score["matched_drugs"]))
            
            if score["matched_fraud"]:
                st.write("🚨 Fraud")
                st.write(", ".join(score["matched_fraud"]))


            st.write("### Reasons")

            for reason in score["reasons"]:
                st.write(f"• {reason}")
            
            st.write("💊 Drug Investigation Evidence")

            if score["evidence"]:
                for item in score["evidence"]:
                    with st.expander(
                        f"💊 {item['keyword']} | Message {item['message_id']}"):
                        st.write(f"**Date:** {item['date']}")
                        st.write("**Message:**")
                        st.write(item["text"])
            else:
                st.info("No drug evidence found.")



    st.divider()

    if st.button("📥 Scrape Selected Channels"):

        if not scrape_channels:
            st.warning("Please select at least one channel.")

        else:
            with st.spinner("Scraping channels..."):

                scrape_results = asyncio.run(
                scrape_selected_channels(scrape_channels,weights)
            )

        st.success("✅ Scraping Completed Successfully!")
        st.divider()

        for result in scrape_results:
            st.success(result["channel"])
            st.write(
                f"Messages Downloaded : {result['message_count']}"
            )
            st.write(
                f"CSV Saved : {result['csv_path']}"
            )