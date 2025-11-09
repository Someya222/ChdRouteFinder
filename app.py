import streamlit as st
from route_finder import nearest_node_for_point
from locations_config import CHANDIGARH_LOCATIONS
from streamlit_folium import folium_static
import folium
import osmnx as ox
import networkx as nx

# Page configuration
st.set_page_config(
    page_title="Chandigarh Route Optimizer",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Enhanced CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        padding-top: 1rem;
        background: linear-gradient(to bottom, #f8f9fa 0%, #ffffff 100%);
    }
    
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%);
        color: white;
        font-weight: 600;
        border-radius: 12px;
        padding: 1rem;
        border: none;
        font-size: 1.1rem;
        box-shadow: 0 4px 12px rgba(0, 102, 204, 0.2);
        transition: all 0.3s ease;
        margin-top: 1.5rem;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #0052a3 0%, #003d7a 100%);
        box-shadow: 0 6px 16px rgba(0, 102, 204, 0.3);
        transform: translateY(-2px);
    }
    
    h1 {
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 0.5rem;
        font-size: 2.5rem;
        text-align: center;
    }
    
    h2 {
        font-weight: 600;
        color: #2c2c2c;
        font-size: 1.5rem;
        margin-top: 2.5rem;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e9ecef;
    }
    
    .subtitle {
        color: #666;
        font-size: 1.15rem;
        margin-bottom: 3rem;
        text-align: center;
        font-weight: 400;
    }
    
    .location-section {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
    }
    
    .metric-container {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 2rem;
        border-radius: 16px;
        border: 2px solid #e9ecef;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        transition: all 0.3s ease;
    }
    
    .metric-container:hover {
        border-color: #0066cc;
        box-shadow: 0 6px 16px rgba(0,102,204,0.12);
        transform: translateY(-2px);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #0066cc;
        margin: 0;
        line-height: 1;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #666;
        margin-top: 0.5rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    div[data-testid="stSelectbox"] > label {
        font-weight: 600;
        color: #2c2c2c;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    
    div[data-testid="stSelectbox"] > div > div {
        border-radius: 10px;
        border: 2px solid #e9ecef;
        transition: all 0.3s ease;
    }
    
    div[data-testid="stSelectbox"] > div > div:hover {
        border-color: #0066cc;
    }
    
    .summary-box {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        border-left: 5px solid #0066cc;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-top: 2rem;
    }
    
    .summary-box p {
        margin: 0.5rem 0;
        font-size: 1.1rem;
        color: #2c2c2c;
    }
    
    .summary-box strong {
        color: #0066cc;
        font-weight: 600;
    }
    
    .map-container {
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        margin-top: 1.5rem;
    }
    
    .stSpinner > div {
        border-top-color: #0066cc !important;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
session_keys = ["G", "start_node", "end_node", "start_latlon", "end_latlon", "start_name", "end_name"]
for key in session_keys:
    if key not in st.session_state:
        st.session_state[key] = None

# Header
st.title(" Chandigarh Route Optimizer")
st.markdown('<p class="subtitle">Find the shortest route between locations using Dijkstra\'s Algorithm</p>', unsafe_allow_html=True)

# Location Selection in a styled container
st.markdown('<div class="location-section">', unsafe_allow_html=True)
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("###  Start Location")
    start_location = st.selectbox(
        "Choose starting point",
        options=["Select start location..."] + sorted(CHANDIGARH_LOCATIONS.keys()),
        key="start_select",
        index=0,
        label_visibility="collapsed"
    )
    if start_location == "Select start location...":
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()
    start_latlon = CHANDIGARH_LOCATIONS[start_location]

with col2:
    st.markdown("###  Destination")
    end_location = st.selectbox(
        "Choose destination",
        options=["Select destination..."] + sorted(CHANDIGARH_LOCATIONS.keys()),
        key="end_select",
        index=0,
        label_visibility="collapsed"
    )
    if end_location == "Select destination...":
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()
    end_latlon = CHANDIGARH_LOCATIONS[end_location]

# Validation
if start_location == end_location:
    st.error("⚠️ Please select different start and destination locations")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# Find Route Button
if st.button(" Find Shortest Route"):
    st.markdown("</div>", unsafe_allow_html=True)
    
    try:
        # Load Graph
        if st.session_state.G is None:
            with st.spinner("Loading road network data..."):
                center_point = (30.7411, 76.7807)  # Sector 17
                
                G = ox.graph_from_point(
                    center_point,
                    dist=8000,  # 8km radius
                    network_type="drive",
                    simplify=True
                )
                st.session_state.G = G
        else:
            G = st.session_state.G
        
        # Find Nearest Nodes
        with st.spinner("Locating positions on road network..."):
            start_node = nearest_node_for_point(G, start_latlon[0], start_latlon[1])
            end_node = nearest_node_for_point(G, end_latlon[0], end_latlon[1])
            
            if start_node not in G.nodes or end_node not in G.nodes:
                st.error("Unable to locate positions on road network")
                st.stop()
        
        # Save to session
        st.session_state.start_node = start_node
        st.session_state.end_node = end_node
        st.session_state.start_latlon = start_latlon
        st.session_state.end_latlon = end_latlon
        st.session_state.start_name = start_location
        st.session_state.end_name = end_location
        
        # Run shortest path algorithm
        with st.spinner("Computing shortest path using Dijkstra's algorithm..."):
            try:
                route = nx.shortest_path(G, start_node, end_node, weight='length')
                distance_meters = nx.shortest_path_length(G, start_node, end_node, weight='length')
            except nx.NetworkXNoPath:
                st.error("No route found between these locations")
                st.stop()
            except Exception as e:
                st.error(f"Error finding route: {str(e)}")
                st.stop()
        
        if not route or len(route) < 2:
            st.error("No route found between these locations")
            st.stop()
        
        distance_km = distance_meters / 1000
        
        # Display Results
        st.markdown("##  Route Details")
        
        # Metrics in cards
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            st.markdown(f"""
                <div class="metric-container">
                    <p class="metric-value">{distance_km:.2f} km</p>
                    <p class="metric-label">Total Distance</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class="metric-container">
                    <p class="metric-value">{len(route)}</p>
                    <p class="metric-label">Route Points</p>
                </div>
            """, unsafe_allow_html=True)
        
        # Create Map Visualization
        st.markdown("##  Route Visualization")
        
        route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route]
        
        # Calculate proper center and zoom
        lats = [coord[0] for coord in route_coords]
        lons = [coord[1] for coord in route_coords]
        center_lat = (min(lats) + max(lats)) / 2
        center_lon = (min(lons) + max(lons)) / 2
        
        # Calculate appropriate zoom level based on route span
        lat_span = max(lats) - min(lats)
        lon_span = max(lons) - min(lons)
        max_span = max(lat_span, lon_span)
        
        # Dynamic zoom: smaller span = more zoom
        if max_span < 0.02:
            zoom = 14
        elif max_span < 0.05:
            zoom = 13
        elif max_span < 0.1:
            zoom = 12
        else:
            zoom = 11
        
        # Create map with better styling
        route_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom,
            tiles='OpenStreetMap'
        )
        
        # Add route line with better styling
        folium.PolyLine(
            route_coords,
            color="#0066cc",
            weight=6,
            opacity=0.85,
            popup=f"<b>Route:</b> {distance_km:.2f} km"
        ).add_to(route_map)
        
        # Add start marker with name label
        folium.Marker(
            start_latlon,
            popup=f"<div style='font-size: 14px; font-weight: bold;'>START<br>{start_location}</div>",
            tooltip=f"START: {start_location}",
            icon=folium.Icon(color="green", icon="play", prefix='fa')
        ).add_to(route_map)
        
        # Add permanent label for start
        folium.Marker(
            start_latlon,
            icon=folium.DivIcon(html=f"""
                <div style="
                    background-color: white;
                    border: 2px solid #28a745;
                    border-radius: 8px;
                    padding: 4px 8px;
                    font-weight: bold;
                    font-size: 12px;
                    color: #28a745;
                    white-space: nowrap;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                ">
                     {start_location}
                </div>
            """)
        ).add_to(route_map)
        
        # Add end marker with name label
        folium.Marker(
            end_latlon,
            popup=f"<div style='font-size: 14px; font-weight: bold;'>DESTINATION<br>{end_location}</div>",
            tooltip=f"DESTINATION: {end_location}",
            icon=folium.Icon(color="red", icon="stop", prefix='fa')
        ).add_to(route_map)
        
        # Add permanent label for end
        folium.Marker(
            end_latlon,
            icon=folium.DivIcon(html=f"""
                <div style="
                    background-color: white;
                    border: 2px solid #dc3545;
                    border-radius: 8px;
                    padding: 4px 8px;
                    font-weight: bold;
                    font-size: 12px;
                    color: #dc3545;
                    white-space: nowrap;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                ">
                     {end_location}
                </div>
            """)
        ).add_to(route_map)
        
        # Display map in styled container
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        folium_static(route_map, width=1200, height=650)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Route Summary
        st.markdown("##  Summary")
        st.markdown(f"""
            <div class="summary-box">
                <p><strong>From:</strong> {start_location}</p>
                <p><strong>To:</strong> {end_location}</p>
                <p><strong>Distance:</strong> {distance_km:.2f} km ({distance_meters:.0f} meters)</p>
                <p><strong>Algorithm:</strong> Dijkstra's Shortest Path</p>
            </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        with st.expander("Error Details"):
            import traceback
            st.code(traceback.format_exc())

else:
    st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
    <div style='text-align: center; color: #999; padding: 2rem 0; border-top: 2px solid #e9ecef; margin-top: 3rem;'>
        <p style='margin: 0; font-size: 0.95rem;'>Powered by Dijkstra's Algorithm | Data from OpenStreetMap</p>
    </div>
""", unsafe_allow_html=True)