// LAE Schedule System - Frontend Application

function laeApp() {
    return {
        // 当前视图状态
        currentView: 'summary',
        
        // 日期状态
        currentDate: new Date(),
        currentWeekStart: null,
        currentMonth: new Date().getMonth() + 1,
        currentYear: new Date().getFullYear(),
        
        // 数据状态
        activities: [],
        flatActivities: [],
        weekSchedule: {},
        monthSchedule: {},
        
        // 时间槽配置
        timeSlots: [
            { value: 21, name: '上午第1时段' },
            { value: 22, name: '上午第2时段' },
            { value: 51, name: '下午第1时段' },
            { value: 52, name: '下午第2时段' },
            { value: 71, name: '晚上时段' }
        ],
        
        // 模态框状态
        showNewActivityModal: false,
        showEditEventModal: false,
        
        // 表单数据
        newActivity: {
            name: '',
            parent_id: '',
            description: ''
        },
        
        editingEvent: {
            id: null,
            activity_id: null,
            activity_name: '',
            event_date: '',
            time_slot: 21,
            goal: '',
            notes: '',
            status: 'planned'
        },
        
        // 周数据
        weekDates: [],
        
        // 初始化
        async init() {
            await this.loadActivities();
            this.updateWeekDates();
            this.initDragAndDrop();
            
            // 根据当前视图加载数据
            if (this.currentView === 'week') {
                await this.loadWeekSchedule();
            } else if (this.currentView === 'month') {
                await this.loadMonthSchedule();
            }
        },
        
        // API调用方法
        async apiCall(endpoint, options = {}) {
            try {
                const response = await fetch(`/api${endpoint}`, {
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    },
                    ...options
                });
                
                if (!response.ok) {
                    throw new Error(`API错误: ${response.status}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error('API调用失败:', error);
                alert('操作失败: ' + error.message);
                throw error;
            }
        },
        
        // 加载活动数据
        async loadActivities() {
            try {
                this.activities = await this.apiCall('/activities/tree');
                this.flatActivities = await this.apiCall('/activities/');
            } catch (error) {
                console.error('加载活动失败:', error);
            }
        },
        
        // 创建新活动
        async createActivity() {
            try {
                const activityData = {
                    name: this.newActivity.name,
                    description: this.newActivity.description || null,
                    parent_id: this.newActivity.parent_id || null
                };
                
                await this.apiCall('/activities/', {
                    method: 'POST',
                    body: JSON.stringify(activityData)
                });
                
                // 重新加载数据
                await this.loadActivities();
                
                // 关闭模态框并重置表单
                this.showNewActivityModal = false;
                this.newActivity = { name: '', parent_id: '', description: '' };
                
            } catch (error) {
                console.error('创建活动失败:', error);
            }
        },
        
        // 视图切换
        async switchView(view) {
            this.currentView = view;
            
            if (view === 'week') {
                await this.loadWeekSchedule();
            } else if (view === 'month') {
                await this.loadMonthSchedule();
            }
        },
        
        // 周视图相关方法
        updateWeekDates() {
            const start = new Date(this.currentDate);
            start.setDate(start.getDate() - start.getDay() + 1); // 获取周一
            this.currentWeekStart = new Date(start);
            
            this.weekDates = [];
            for (let i = 0; i < 7; i++) {
                const date = new Date(start);
                date.setDate(start.getDate() + i);
                this.weekDates.push(date.toISOString().split('T')[0]);
            }
        },
        
        async loadWeekSchedule() {
            try {
                const targetDate = this.weekDates[0]; // 周一
                const data = await this.apiCall(`/calendar/week/${targetDate}`);
                
                // 转换数据格式以便查找
                this.weekSchedule = {};
                data.schedule.forEach(day => {
                    this.weekSchedule[day.date] = day.slots;
                });
            } catch (error) {
                console.error('加载周日程失败:', error);
            }
        },
        
        getScheduledEvent(date, timeSlot) {
            return this.weekSchedule[date]?.[timeSlot] || null;
        },
        
        previousWeek() {
            this.currentDate.setDate(this.currentDate.getDate() - 7);
            this.updateWeekDates();
            this.loadWeekSchedule();
        },
        
        nextWeek() {
            this.currentDate.setDate(this.currentDate.getDate() + 7);
            this.updateWeekDates();
            this.loadWeekSchedule();
        },
        
        // 月视图相关方法
        async loadMonthSchedule() {
            try {
                const data = await this.apiCall(`/calendar/month/${this.currentYear}/${this.currentMonth}`);
                this.monthSchedule = data;
                this.renderMonthCalendar();
            } catch (error) {
                console.error('加载月日程失败:', error);
            }
        },
        
        previousMonth() {
            this.currentMonth--;
            if (this.currentMonth < 1) {
                this.currentMonth = 12;
                this.currentYear--;
            }
            this.loadMonthSchedule();
        },
        
        nextMonth() {
            this.currentMonth++;
            if (this.currentMonth > 12) {
                this.currentMonth = 1;
                this.currentYear++;
            }
            this.loadMonthSchedule();
        },
        
        renderMonthCalendar() {
            if (!this.monthSchedule.days) return;
            
            const calendarDiv = document.getElementById('month-calendar');
            let html = '';
            
            // 计算第一天是周几，调整显示
            const firstDay = new Date(this.currentYear, this.currentMonth - 1, 1);
            const startPadding = (firstDay.getDay() + 6) % 7; // 转换为周一开始
            
            // 添加空白天数
            for (let i = 0; i < startPadding; i++) {
                html += '<div class="col border" style="height: 100px;"></div>';
            }
            
            // 添加每一天
            this.monthSchedule.days.forEach(day => {
                const isToday = day.is_today ? 'bg-primary text-white' : '';
                const hasEvents = day.event_count > 0 ? 'border-warning border-2' : '';
                
                html += `
                    <div class="col border ${hasEvents} ${isToday}" style="height: 100px; cursor: pointer;" 
                         onclick="laeApp().goToWeek('${day.date}')">
                        <div class="p-2">
                            <div class="fw-bold">${day.day}</div>
                            ${day.event_count > 0 ? `<small class="badge bg-secondary">${day.event_count}项</small>` : ''}
                        </div>
                    </div>
                `;
            });
            
            calendarDiv.innerHTML = `<div class="row g-0">${html}</div>`;
        },
        
        goToWeek(dateString) {
            this.currentDate = new Date(dateString);
            this.updateWeekDates();
            this.switchView('week');
        },
        
        // 日程编辑
        editScheduledEvent(date, timeSlot) {
            const event = this.getScheduledEvent(date, timeSlot);
            
            if (event) {
                // 编辑现有事件
                this.editingEvent = {
                    id: event.id,
                    activity_id: event.activity_id,
                    activity_name: event.activity_name,
                    event_date: date,
                    time_slot: timeSlot,
                    goal: event.goal || '',
                    notes: event.notes || '',
                    status: event.status
                };
            } else {
                // 创建新事件（但需要先选择活动）
                this.editingEvent = {
                    id: null,
                    activity_id: null,
                    activity_name: '',
                    event_date: date,
                    time_slot: timeSlot,
                    goal: '',
                    notes: '',
                    status: 'planned'
                };
            }
            
            this.showEditEventModal = true;
        },
        
        async saveScheduledEvent() {
            try {
                if (!this.editingEvent.activity_id) {
                    alert('请先拖拽活动到时间槽中');
                    return;
                }
                
                const eventData = {
                    activity_id: this.editingEvent.activity_id,
                    event_date: this.editingEvent.event_date,
                    time_slot: this.editingEvent.time_slot,
                    goal: this.editingEvent.goal || null,
                    notes: this.editingEvent.notes || null,
                    status: this.editingEvent.status
                };
                
                if (this.editingEvent.id) {
                    // 更新现有事件
                    await this.apiCall(`/events/${this.editingEvent.id}`, {
                        method: 'PUT',
                        body: JSON.stringify(eventData)
                    });
                } else {
                    // 创建新事件
                    await this.apiCall('/events/', {
                        method: 'POST',
                        body: JSON.stringify(eventData)
                    });
                }
                
                // 刷新数据
                await this.loadWeekSchedule();
                this.showEditEventModal = false;
                
            } catch (error) {
                console.error('保存日程失败:', error);
            }
        },
        
        async deleteScheduledEvent() {
            if (!this.editingEvent.id) return;
            
            if (confirm('确定要删除这个日程吗？')) {
                try {
                    await this.apiCall(`/events/${this.editingEvent.id}`, {
                        method: 'DELETE'
                    });
                    
                    await this.loadWeekSchedule();
                    this.showEditEventModal = false;
                } catch (error) {
                    console.error('删除日程失败:', error);
                }
            }
        },
        
        // 拖拽功能初始化
        initDragAndDrop() {
            this.$nextTick(() => {
                // 初始化活动池的拖拽
                const activityPool = document.getElementById('activity-pool');
                if (activityPool) {
                    Sortable.create(activityPool, {
                        group: {
                            name: 'activities',
                            pull: 'clone',
                            put: false
                        },
                        sort: false,
                        ghostClass: 'opacity-50'
                    });
                }
                
                // 初始化时间槽的拖拽接收
                document.querySelectorAll('.time-slot').forEach(slot => {
                    Sortable.create(slot, {
                        group: {
                            name: 'activities',
                            pull: false,
                            put: true
                        },
                        onAdd: (evt) => {
                            const activityId = evt.item.getAttribute('data-activity-id');
                            const date = evt.to.getAttribute('data-date');
                            const timeSlot = parseInt(evt.to.getAttribute('data-time-slot'));
                            
                            // 移除拖拽的元素
                            evt.item.remove();
                            
                            // 处理拖拽放置
                            this.handleDrop(activityId, date, timeSlot);
                        }
                    });
                });
            });
        },
        
        async handleDrop(activityId, date, timeSlot) {
            try {
                // 检查是否已有事件
                const existing = this.getScheduledEvent(date, timeSlot);
                if (existing) {
                    alert('该时间槽已有安排，请选择其他时间或先删除现有安排');
                    return;
                }
                
                // 找到活动信息
                const activity = this.flatActivities.find(a => a.id == activityId);
                if (!activity) {
                    alert('未找到活动信息');
                    return;
                }
                
                // 创建新的日程事件
                const eventData = {
                    activity_id: parseInt(activityId),
                    event_date: date,
                    time_slot: timeSlot,
                    goal: '',
                    notes: '',
                    status: 'planned'
                };
                
                await this.apiCall('/events/', {
                    method: 'POST',
                    body: JSON.stringify(eventData)
                });
                
                // 刷新数据
                await this.loadWeekSchedule();
                
                // 立即打开编辑框让用户添加目标和备注
                setTimeout(() => {
                    this.editScheduledEvent(date, timeSlot);
                }, 100);
                
            } catch (error) {
                console.error('处理拖拽失败:', error);
            }
        },
        
        // 汇总视图渲染
        renderActivityTree() {
            if (!this.activities.length) return '<p class="text-muted">暂无活动</p>';
            
            const renderNode = (activity, level = 0) => {
                const indent = '  '.repeat(level);
                let html = `
                    <div class="mb-2" style="margin-left: ${level * 20}px;">
                        <div class="d-flex justify-content-between align-items-center border-bottom pb-2">
                            <div>
                                <strong>${activity.name}</strong>
                                ${activity.description ? `<br><small class="text-muted">${activity.description}</small>` : ''}
                            </div>
                            <div class="text-end">
                                <button class="btn btn-outline-primary btn-sm me-1" 
                                        onclick="laeApp().editActivity(${activity.id})">
                                    编辑
                                </button>
                                <button class="btn btn-outline-danger btn-sm" 
                                        onclick="laeApp().deleteActivity(${activity.id})">
                                    删除
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                
                if (activity.children && activity.children.length > 0) {
                    activity.children.forEach(child => {
                        html += renderNode(child, level + 1);
                    });
                }
                
                return html;
            };
            
            return this.activities.map(activity => renderNode(activity)).join('');
        },
        
        // 工具方法
        getCurrentDateString() {
            return this.currentDate.toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                weekday: 'long'
            });
        },
        
        getWeekTitle() {
            if (this.weekDates.length === 0) return '';
            const start = new Date(this.weekDates[0]);
            const end = new Date(this.weekDates[6]);
            return `${start.getMonth() + 1}月${start.getDate()}日 - ${end.getMonth() + 1}月${end.getDate()}日`;
        },
        
        getMonthTitle() {
            return `${this.currentYear}年${this.currentMonth}月`;
        },
        
        formatWeekday(dateString) {
            const date = new Date(dateString);
            return ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][date.getDay() === 0 ? 6 : date.getDay() - 1];
        },
        
        formatDate(dateString) {
            const date = new Date(dateString);
            return `${date.getMonth() + 1}/${date.getDate()}`;
        }
    }
}

// 确保函数在全局范围内可用
window.laeApp = laeApp;