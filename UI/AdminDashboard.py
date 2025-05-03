import sys
import firebase_admin
from firebase_admin import credentials, db
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QScrollArea, QPushButton, QSizePolicy,
    QProgressBar, QMessageBox, QToolTip
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QFont, QCursor
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis, QLineSeries
from datetime import datetime, timedelta
import calendar
import os

class MetricCard(QFrame):
    def __init__(self, title, value, icon, color="#4CAF50", show_progress=False, progress_value=0):
        super().__init__()
        self.setObjectName("metricCard")
        self.setStyleSheet(f"""
            #metricCard {{
                background: white;
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
                border: 1px solid #e0e0e0;
            }}
            QLabel {{
                color: #333;
            }}
            QProgressBar {{
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 5px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        # Header with icon and title
        header = QHBoxLayout()
        iconLabel = QLabel(icon)
        iconLabel.setStyleSheet(f"color: {color}; font-size: 24px;")
        titleLabel = QLabel(title)
        titleLabel.setStyleSheet("font-weight: bold; font-size: 14px;")
        header.addWidget(iconLabel)
        header.addWidget(titleLabel)
        header.addStretch()
        
        # Value
        self.valueLabel = QLabel(str(value))
        self.valueLabel.setStyleSheet(f"font-size: 24px; color: {color}; font-weight: bold;")
        
        layout.addLayout(header)
        layout.addWidget(self.valueLabel)
        
        # Progress bar (optional)
        if show_progress:
            self.progressBar = QProgressBar()
            self.progressBar.setMaximum(100)
            self.progressBar.setValue(int(progress_value))
            layout.addWidget(self.progressBar)
        
    def update_value(self, value, progress_value=None):
        self.valueLabel.setText(str(value))
        if hasattr(self, 'progressBar') and progress_value is not None:
            self.progressBar.setValue(int(progress_value))

class AdminDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Dashboard")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize Firebase if not already initialized
        try:
            if not firebase_admin._apps:
                cred_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db', 'farm-management-FireBase_credentials.json')
                print(f"Looking for credentials at: {cred_path}")
                if not os.path.exists(cred_path):
                    print(f"Error: Credentials file not found at {cred_path}")
                    raise FileNotFoundError(f"Credentials file not found at {cred_path}")
                
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': 'https://farm-management-4518e-default-rtdb.firebaseio.com/'
                })
                print("Firebase initialized successfully")
        except Exception as e:
            print(f"Error initializing Firebase: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to initialize Firebase: {str(e)}")
        
        # Create main layout with scroll area
        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Dashboard title
        title = QLabel("🍄 לוח בקרה - רווחים והזמנות")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px 0;")
        scroll_layout.addWidget(title)
        
        # Create grid for metric cards
        metrics_grid = QGridLayout()
        
        # Initialize metric cards with new KPIs
        self.monthly_revenue_card = MetricCard("הכנסות חודשיות", "₪0", "💰", "#E91E63")
        self.monthly_profit_card = MetricCard("רווח חודשי", "₪0", "💵", "#4CAF50")
        self.yearly_revenue_card = MetricCard("הכנסות שנתיות", "₪0", "📊", "#2196F3")
        self.yearly_profit_card = MetricCard("רווח שנתי", "₪0", "📈", "#9C27B0")
        self.avg_order_value = MetricCard("ערך הזמנה ממוצע", "₪0", "🛒", "#FF9800")
        self.total_orders = MetricCard("סה״כ הזמנות", "0", "📦", "#00BCD4")
        self.active_beds_card = MetricCard("מיטות פעילות", "0", "🌱", "#4CAF50", True, 0)
        self.harvest_ready_card = MetricCard("מוכנות לקטיף", "0", "🍄", "#FF9800", True, 0)
        
        # Add cards to grid (3x3 layout)
        metrics_grid.addWidget(self.monthly_revenue_card, 0, 0)
        metrics_grid.addWidget(self.monthly_profit_card, 0, 1)
        metrics_grid.addWidget(self.yearly_revenue_card, 0, 2)
        metrics_grid.addWidget(self.yearly_profit_card, 1, 0)
        metrics_grid.addWidget(self.avg_order_value, 1, 1)
        metrics_grid.addWidget(self.total_orders, 1, 2)
        metrics_grid.addWidget(self.active_beds_card, 2, 0)
        metrics_grid.addWidget(self.harvest_ready_card, 2, 1)
        
        scroll_layout.addLayout(metrics_grid)
        
        # Add charts section
        charts_layout = QGridLayout()
        
        # Revenue and profit trend chart
        self.profit_chart = QChartView()
        self.profit_chart.setMinimumHeight(300)
        charts_layout.addWidget(self.profit_chart, 0, 0)
        
        # Growing beds status chart
        self.beds_chart = QChartView()
        self.beds_chart.setMinimumHeight(300)
        charts_layout.addWidget(self.beds_chart, 0, 1)
        
        # Order value distribution chart
        self.orders_chart = QChartView()
        self.orders_chart.setMinimumHeight(300)
        charts_layout.addWidget(self.orders_chart, 1, 0, 1, 2)
        
        scroll_layout.addLayout(charts_layout)
        
        # Recent Activity Section
        activity_label = QLabel("פעילות אחרונה")
        activity_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 20px;")
        scroll_layout.addWidget(activity_label)
        
        self.activity_frame = QFrame()
        self.activity_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 10px;
                padding: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        self.activity_layout = QVBoxLayout(self.activity_frame)
        scroll_layout.addWidget(self.activity_frame)
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # Set up update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_dashboard_data)
        self.update_timer.start(300000)  # Update every 5 minutes
        
        # Initial data load
        self.update_dashboard_data()

    def update_dashboard_data(self):
        try:
            print("Starting dashboard data update...")
            # Get reference to Firebase database
            ref = db.reference('/')
            print("Got database reference")
            
            # Get current date for monthly calculations
            now = datetime.now()
            current_month = now.month
            current_year = now.year
            
            # Fetch all necessary data
            print("Fetching data from Firebase...")
            orders_ref = ref.child('Order')
            beds_ref = ref.child('GrowingBed')
            harvests_ref = ref.child('Harvests')
            
            orders_data = orders_ref.get() or {}
            beds_data = beds_ref.get() or {}
            harvests_data = harvests_ref.get() or {}
            
            print(f"Retrieved data: Orders: {type(orders_data)}, Beds: {type(beds_data)}, Harvests: {type(harvests_data)}")
            
            # Initialize metrics
            monthly_revenue = 0
            monthly_profit = 0
            yearly_revenue = 0
            yearly_profit = 0
            total_orders_count = 0
            total_order_value = 0
            total_beds = 0
            active_beds = 0
            harvest_ready = 0
            bed_stages = {
                'Spawn Run': 0,
                'Pinning': 0,
                'Fruiting': 0,
                'Harvesting': 0,
                'Empty': 0
            }
            
            # Process orders
            print("Processing orders...")
            if isinstance(orders_data, dict):
                total_orders_count = len(orders_data)
                for order_id, order in orders_data.items():
                    try:
                        if isinstance(order, dict):
                            order_date = order.get('OrderDate', '')
                            if order_date:
                                order_date = datetime.strptime(order_date, '%Y-%m-%d')
                                total_amount = float(order.get('TotalAmount', 0))
                                cost = float(order.get('Cost', 0))  # Assuming we have a Cost field
                                profit = total_amount - cost
                                
                                total_order_value += total_amount
                                
                                if order_date.year == current_year:
                                    yearly_revenue += total_amount
                                    yearly_profit += profit
                                    if order_date.month == current_month:
                                        monthly_revenue += total_amount
                                        monthly_profit += profit
                    except (ValueError, TypeError) as e:
                        print(f"Error processing order {order_id}: {str(e)}")
                        continue
            
            # Calculate average order value
            avg_order_value = total_order_value / total_orders_count if total_orders_count > 0 else 0
            
            # Process beds
            print("Processing beds...")
            if isinstance(beds_data, dict):
                total_beds = len(beds_data)
                for bed_id, bed in beds_data.items():
                    try:
                        if isinstance(bed, dict):
                            stage = bed.get('CurrentGrowthStage', 'Empty')
                            if stage in bed_stages:
                                bed_stages[stage] += 1
                                if stage != 'Empty':
                                    active_beds += 1
                                if stage == 'Harvesting':
                                    harvest_ready += 1
                    except Exception as e:
                        print(f"Error processing bed {bed_id}: {str(e)}")
                        continue
            
            # Calculate percentages
            active_beds_percentage = round((active_beds / total_beds * 100)) if total_beds > 0 else 0
            harvest_ready_percentage = round((harvest_ready / total_beds * 100)) if total_beds > 0 else 0
            
            # Update metric cards
            print("Updating metric cards...")
            self.monthly_revenue_card.update_value(f"₪{monthly_revenue:,.2f}")
            self.monthly_profit_card.update_value(f"₪{monthly_profit:,.2f}")
            self.yearly_revenue_card.update_value(f"₪{yearly_revenue:,.2f}")
            self.yearly_profit_card.update_value(f"₪{yearly_profit:,.2f}")
            self.avg_order_value.update_value(f"₪{avg_order_value:,.2f}")
            self.total_orders.update_value(str(total_orders_count))
            self.active_beds_card.update_value(f"{active_beds}/{total_beds}", active_beds_percentage)
            self.harvest_ready_card.update_value(f"{harvest_ready}/{total_beds}", harvest_ready_percentage)
            
            # Update charts
            print("Updating charts...")
            self.update_profit_chart(orders_data)
            self.update_beds_chart(bed_stages)
            self.update_orders_chart(orders_data)
            
            # Update recent activity
            print("Updating recent activity...")
            self.update_recent_activity(orders_data, beds_data, harvests_data)
            
            print("Dashboard update completed successfully")
            
        except Exception as e:
            print(f"Error updating dashboard: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Error", f"Failed to update dashboard: {str(e)}")
    
    def update_profit_chart(self, orders_data):
        chart = QChart()
        chart.setTitle("מגמת רווחים והכנסות")
        
        # Create series for revenue and profit
        revenue_series = QLineSeries()
        revenue_series.setName("הכנסות")
        profit_series = QLineSeries()
        profit_series.setName("רווח")
        
        # Get last 6 months
        months = []
        revenues = []
        profits = []
        now = datetime.now()
        
        for i in range(5, -1, -1):
            date = now - timedelta(days=i*30)
            month_name = calendar.month_abbr[date.month]
            months.append(month_name)
            
            # Calculate revenue and profit for this month
            monthly_revenue = 0
            monthly_profit = 0
            if isinstance(orders_data, dict):
                for order in orders_data.values():
                    try:
                        if isinstance(order, dict):
                            order_date = datetime.strptime(order.get('OrderDate', ''), '%Y-%m-%d')
                            if order_date.month == date.month and order_date.year == date.year:
                                total_amount = float(order.get('TotalAmount', 0))
                                cost = float(order.get('Cost', 0))
                                monthly_revenue += total_amount
                                monthly_profit += (total_amount - cost)
                    except (ValueError, TypeError):
                        continue
            
            revenues.append(monthly_revenue)
            profits.append(monthly_profit)
        
        # Add data to series
        for i, (rev, prof) in enumerate(zip(revenues, profits)):
            revenue_series.append(i, rev)
            profit_series.append(i, prof)
        
        # Add tooltips to series
        for i, (rev, prof) in enumerate(zip(revenues, profits)):
            revenue_series.setPointLabelsVisible(True)
            revenue_series.setPointLabelsFormat(f"₪{rev:,.0f}")
            profit_series.setPointLabelsVisible(True)
            profit_series.setPointLabelsFormat(f"₪{prof:,.0f}")
        
        chart.addSeries(revenue_series)
        chart.addSeries(profit_series)
        
        # Set up axes
        axis_x = QValueAxis()
        axis_x.setRange(0, 5)
        axis_x.setTickCount(6)
        axis_x.setLabelFormat("%s")
        axis_x.setLabelsAngle(-45)
        chart.addAxis(axis_x, Qt.AlignBottom)
        revenue_series.attachAxis(axis_x)
        profit_series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        chart.addAxis(axis_y, Qt.AlignLeft)
        revenue_series.attachAxis(axis_y)
        profit_series.attachAxis(axis_y)
        
        # Enable hover effects
        chart.setAcceptHoverEvents(True)
        chart.setCursor(Qt.PointingHandCursor)
        
        # Add hover tooltips
        def hover_changed(point, state):
            if state:
                tooltip = f"חודש: {months[int(point.x())]}\n"
                tooltip += f"הכנסות: ₪{revenues[int(point.x())]:,.0f}\n"
                tooltip += f"רווח: ₪{profits[int(point.x())]:,.0f}"
                QToolTip.showText(QCursor.pos(), tooltip)
            else:
                QToolTip.hideText()
        
        revenue_series.hovered.connect(hover_changed)
        profit_series.hovered.connect(hover_changed)
        
        self.profit_chart.setChart(chart)
    
    def update_orders_chart(self, orders_data):
        chart = QChart()
        chart.setTitle("התפלגות ערכי הזמנות")
        
        # Create bar series
        series = QBarSeries()
        order_set = QBarSet("ערך הזמנה")
        
        # Define value ranges
        ranges = [
            (0, 1000),
            (1000, 2000),
            (2000, 5000),
            (5000, 10000),
            (10000, float('inf'))
        ]
        
        # Count orders in each range
        counts = [0] * len(ranges)
        if isinstance(orders_data, dict):
            for order in orders_data.values():
                try:
                    if isinstance(order, dict):
                        amount = float(order.get('TotalAmount', 0))
                        for i, (min_val, max_val) in enumerate(ranges):
                            if min_val <= amount < max_val:
                                counts[i] += 1
                                break
                except (ValueError, TypeError):
                    continue
        
        # Add data to bar set
        order_set.append(counts)
        series.append(order_set)
        chart.addSeries(series)
        
        # Add tooltips to bars
        for i, count in enumerate(counts):
            order_set.setLabel(f"{count} הזמנות")
        
        # Set up axes
        axis_x = QBarCategoryAxis()
        axis_x.append(["0-1,000", "1,000-2,000", "2,000-5,000", "5,000-10,000", "10,000+"])
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        # Enable hover effects
        chart.setAcceptHoverEvents(True)
        chart.setCursor(Qt.PointingHandCursor)
        
        # Add hover tooltips
        def hover_changed(status, index, barset):
            if status:
                range_text = ["0-1,000", "1,000-2,000", "2,000-5,000", "5,000-10,000", "10,000+"][index]
                tooltip = f"טווח: {range_text}\n"
                tooltip += f"מספר הזמנות: {counts[index]}"
                QToolTip.showText(QCursor.pos(), tooltip)
            else:
                QToolTip.hideText()
        
        series.hovered.connect(hover_changed)
        
        self.orders_chart.setChart(chart)
    
    def update_beds_chart(self, bed_stages):
        chart = QChart()
        chart.setTitle("סטטוס מיטות גידול")
        
        # Remove grid lines and adjust layout
        chart.setBackgroundVisible(False)
        chart.setPlotAreaBackgroundVisible(False)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignRight)  # Move legend to right side
        
        series = QPieSeries()
        
        # Hebrew labels and colors for each stage
        stage_labels = {
            'Spawn Run': 'ריצת נבגים',
            'Pinning': 'הנצה',
            'Fruiting': 'פריחה',
            'Harvesting': 'קטיף',
            'Empty': 'ריק'
        }
        
        colors = {
            'Spawn Run': '#4e73df',    # Blue
            'Pinning': '#f6c23e',      # Yellow
            'Fruiting': '#1cc88a',     # Green
            'Harvesting': '#e74a3b',   # Red
            'Empty': '#858796'         # Gray
        }
        
        total_beds = sum(bed_stages.values())
        
        for stage, count in bed_stages.items():
            if count > 0:  # Only add non-zero values
                percentage = (count / total_beds) * 100 if total_beds > 0 else 0
                hebrew_label = stage_labels.get(stage, stage)
                slice = series.append(f"{hebrew_label}", count)
                slice.setBrush(QColor(colors.get(stage, '#000000')))
                slice.setLabelVisible(True)
                slice.setLabel(f"{hebrew_label}: {count} ({percentage:.1f}%)")
                slice.setLabelFont(QFont("Arial", 10))  # Set font size for better readability
                slice.setExploded(True)  # Slightly explode all slices for better visibility
                slice.setExplodeDistanceFactor(0.05)  # Small explosion factor
        
        chart.addSeries(series)
        
        # Set chart title font and style
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        chart.setTitleFont(title_font)
        
        # Enable hover effects
        for slice in series.slices():
            slice.hovered.connect(lambda state, slice=slice: self.handle_slice_hover(state, slice))
        
        self.beds_chart.setChart(chart)
    
    def handle_slice_hover(self, state, slice):
        """Handle hover events for pie chart slices"""
        if state:
            # Increase explosion factor on hover
            slice.setExplodeDistanceFactor(0.15)
            percentage = (slice.percentage() * 100)
            tooltip = f"{slice.label()}\nאחוז: {percentage:.1f}%"
            QToolTip.showText(QCursor.pos(), tooltip)
        else:
            # Reset explosion factor
            slice.setExplodeDistanceFactor(0.05)
            QToolTip.hideText()
    
    def update_recent_activity(self, orders_data, beds_data, harvests_data):
        # Clear existing activity items
        for i in reversed(range(self.activity_layout.count())): 
            self.activity_layout.itemAt(i).widget().setParent(None)
        
        activities = []
        
        # Add recent orders
        if isinstance(orders_data, dict):
            try:
                for order_id, order in orders_data.items():
                    if isinstance(order, dict):
                        try:
                            order_date = order.get('OrderDate', '')
                            if order_date:
                                activities.append((
                                    order_date,
                                    f"📦 Order #{order_id}: ₪{float(order.get('TotalAmount', 0)):,.2f}"
                                ))
                        except (ValueError, TypeError) as e:
                            print(f"Error processing order activity {order_id}: {str(e)}")
            except Exception as e:
                print(f"Error processing orders for activity: {str(e)}")
        
        # Add bed status changes
        if isinstance(beds_data, dict):
            for bed_id, bed in beds_data.items():
                if isinstance(bed, dict):
                    try:
                        stage = bed.get('CurrentGrowthStage', '')
                        last_updated = bed.get('LastUpdated', '')
                        if stage and last_updated:
                            if stage == 'Harvesting':
                                activities.append((
                                    last_updated,
                                    f"🍄 Bed #{bed_id} ready for harvest!"
                                ))
                            elif stage == 'Fruiting':
                                activities.append((
                                    last_updated,
                                    f"🌱 Bed #{bed_id} in fruiting phase"
                                ))
                    except Exception as e:
                        print(f"Error processing bed activity {bed_id}: {str(e)}")
        
        # Add recent harvests
        if isinstance(harvests_data, dict):
            try:
                for harvest_id, harvest in harvests_data.items():
                    if isinstance(harvest, dict):
                        try:
                            harvest_date = harvest.get('date', '')
                            if harvest_date:
                                activities.append((
                                    harvest_date,
                                    f"⚖️ Harvest #{harvest_id}: {harvest.get('quantity', 0)}kg"
                                ))
                        except (ValueError, TypeError) as e:
                            print(f"Error processing harvest activity {harvest_id}: {str(e)}")
            except Exception as e:
                print(f"Error processing harvests for activity: {str(e)}")
        
        # Sort activities by date and display
        activities.sort(key=lambda x: x[0], reverse=True)
        for date, message in activities[:10]:
            activity = QLabel(f"{date}: {message}")
            activity.setStyleSheet("color: #333; padding: 5px 0;")
            self.activity_layout.addWidget(activity)

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    # Apply style to the entire application
    app.setStyleSheet("""
        QWidget {
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
        }
    """)
    
    dashboard = AdminDashboard()
    dashboard.show()
    sys.exit(app.exec_()) 