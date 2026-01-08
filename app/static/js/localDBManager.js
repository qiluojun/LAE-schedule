/**
 * LAE Local Database Manager - IndexedDB缓存层
 *
 * 功能：
 * 1. 启动时从Supabase下载完整数据到IndexedDB
 * 2. 运行时所有操作在本地IndexedDB执行（超快速）
 * 3. 退出时将更改同步回Supabase
 *
 * 使用方法：
 *   const db = new LocalDBManager();
 *   await db.init();
 *   await db.downloadFromCloud();
 *   const events = await db.query('scheduled_events', { event_date: '2025-01-08' });
 *   await db.syncToCloud();
 */

class LocalDBManager {
    constructor() {
        this.db = null;
        this.dbName = 'LAE_LocalCache';
        this.version = 2; // 🔧 升级到版本2，添加autoIncrement
        this.isDirty = false; // 标记是否有未同步的更改
        this.changeLog = []; // 记录所有更改操作
        this.isInitialized = false;
    }

    // ==========================================
    // 1. 初始化IndexedDB
    // ==========================================
    async init() {
        if (this.isInitialized) {
            console.log('⚠️ IndexedDB已初始化，跳过');
            return this.db;
        }

        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.version);

            request.onerror = () => {
                console.error('❌ IndexedDB初始化失败:', request.error);
                reject(request.error);
            };

            request.onsuccess = () => {
                this.db = request.result;
                this.isInitialized = true;
                console.log('✅ IndexedDB初始化成功');
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                const oldVersion = event.oldVersion;
                console.log(`🔧 升级IndexedDB: v${oldVersion} → v${event.newVersion}`);

                // 🔧 V2升级：删除旧表，重新创建带autoIncrement的表
                if (oldVersion < 2) {
                    console.log('🔄 迁移到V2: 添加autoIncrement支持');

                    // 删除旧表
                    const oldStores = ['scheduled_events', 'domains', 'activity_types', 'schedules', 'activities'];
                    oldStores.forEach(storeName => {
                        if (db.objectStoreNames.contains(storeName)) {
                            db.deleteObjectStore(storeName);
                            console.log(`  🗑️ 删除旧表: ${storeName}`);
                        }
                    });
                }

                // 创建scheduled_events表（带autoIncrement）
                if (!db.objectStoreNames.contains('scheduled_events')) {
                    const eventStore = db.createObjectStore('scheduled_events', {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    eventStore.createIndex('event_date', 'event_date', { unique: false });
                    eventStore.createIndex('time_slot', 'time_slot', { unique: false });
                    eventStore.createIndex('date_slot', ['event_date', 'time_slot'], { unique: false });
                    console.log('  ✓ scheduled_events表创建完成 (autoIncrement)');
                }

                // 创建domains表（带autoIncrement）
                if (!db.objectStoreNames.contains('domains')) {
                    db.createObjectStore('domains', {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    console.log('  ✓ domains表创建完成 (autoIncrement)');
                }

                // 创建activity_types表（带autoIncrement）
                if (!db.objectStoreNames.contains('activity_types')) {
                    db.createObjectStore('activity_types', {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    console.log('  ✓ activity_types表创建完成 (autoIncrement)');
                }

                // 创建schedules表（带autoIncrement）
                if (!db.objectStoreNames.contains('schedules')) {
                    db.createObjectStore('schedules', {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    console.log('  ✓ schedules表创建完成 (autoIncrement)');
                }

                // 创建activities表（V1兼容，带autoIncrement）
                if (!db.objectStoreNames.contains('activities')) {
                    db.createObjectStore('activities', {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    console.log('  ✓ activities表创建完成 (autoIncrement)');
                }

                // 创建元数据表
                if (!db.objectStoreNames.contains('_metadata')) {
                    db.createObjectStore('_metadata', { keyPath: 'key' });
                    console.log('  ✓ _metadata表创建完成');
                }

                console.log('✅ 所有表结构创建完成');
            };
        });
    }

    // ==========================================
    // 2. 从云端下载完整数据
    // ==========================================
    async downloadFromCloud(apiBaseUrl = '/api') {
        console.log('🌐 开始从云端下载数据...');
        const startTime = Date.now();

        try {
            // 并行下载所有表数据
            console.log('  📥 正在下载scheduled_events...');
            const eventsPromise = fetch(`${apiBaseUrl}/events/?limit=10000`).then(r => r.json());

            console.log('  📥 正在下载domains...');
            const domainsPromise = fetch(`${apiBaseUrl}/domains/`).then(r => r.json());

            console.log('  📥 正在下载activity_types...');
            const typesPromise = fetch(`${apiBaseUrl}/activity-types/`).then(r => r.json());

            console.log('  📥 正在下载schedules...');
            const schedulesPromise = fetch(`${apiBaseUrl}/schedules/`).then(r => r.json());

            console.log('  📥 正在下载activities...');
            const activitiesPromise = fetch(`${apiBaseUrl}/activities/`).then(r => r.json());

            const [events, domains, types, schedules, activities] = await Promise.all([
                eventsPromise,
                domainsPromise,
                typesPromise,
                schedulesPromise,
                activitiesPromise
            ]);

            // 清空本地数据
            console.log('  🗑️ 清空本地缓存...');
            await this.clearAllStores();

            // 批量插入到IndexedDB
            console.log('  💾 保存到IndexedDB...');
            await this.bulkInsert('scheduled_events', events);
            await this.bulkInsert('domains', domains);
            await this.bulkInsert('activity_types', types);
            await this.bulkInsert('schedules', schedules);
            await this.bulkInsert('activities', activities);

            // 记录同步时间
            await this.setMetadata('last_sync', new Date().toISOString());
            await this.setMetadata('is_synced', true);

            // 清空更改日志
            this.isDirty = false;
            this.changeLog = [];

            const elapsed = Date.now() - startTime;
            console.log(`✅ 数据下载完成！用时: ${elapsed}ms`);
            console.log(`📊 数据量统计:`);
            console.log(`   - Events: ${events.length}`);
            console.log(`   - Domains: ${domains.length}`);
            console.log(`   - Types: ${types.length}`);
            console.log(`   - Schedules: ${schedules.length}`);
            console.log(`   - Activities: ${activities.length}`);

            return {
                success: true,
                elapsed,
                counts: {
                    events: events.length,
                    domains: domains.length,
                    types: types.length,
                    schedules: schedules.length,
                    activities: activities.length
                }
            };
        } catch (error) {
            console.error('❌ 下载数据失败:', error);
            throw error;
        }
    }

    // ==========================================
    // 3. 批量插入数据
    // ==========================================
    async bulkInsert(storeName, records) {
        // 🔧 修复：确保records是数组
        if (!records) {
            console.log(`⚠️ ${storeName}: 无数据需要插入 (records is null/undefined)`);
            return;
        }

        // 如果不是数组，尝试转换
        if (!Array.isArray(records)) {
            console.warn(`⚠️ ${storeName}: records不是数组，尝试转换...`, typeof records);
            // 可能是对象，尝试提取数据
            if (records.data && Array.isArray(records.data)) {
                records = records.data;
            } else if (records.items && Array.isArray(records.items)) {
                records = records.items;
            } else {
                console.error(`❌ ${storeName}: 无法转换为数组`, records);
                return;
            }
        }

        if (records.length === 0) {
            console.log(`⚠️ ${storeName}: 无数据需要插入 (empty array)`);
            return;
        }

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);

            let successCount = 0;
            let errorCount = 0;

            records.forEach(record => {
                // 🔧 使用put而不是add，这样可以保留云端的ID
                // put会更新已存在的记录或插入新记录
                const request = store.put(record);
                request.onsuccess = () => successCount++;
                request.onerror = () => {
                    errorCount++;
                    console.warn(`插入失败:`, record, request.error);
                };
            });

            transaction.oncomplete = () => {
                console.log(`  ✓ ${storeName}: ${successCount}条记录插入成功`);
                if (errorCount > 0) {
                    console.warn(`  ⚠️ ${storeName}: ${errorCount}条记录插入失败`);
                }
                resolve();
            };

            transaction.onerror = () => {
                console.error(`❌ ${storeName}批量插入失败:`, transaction.error);
                reject(transaction.error);
            };
        });
    }

    // ==========================================
    // 4. 清空所有数据
    // ==========================================
    async clearAllStores() {
        const storeNames = ['scheduled_events', 'domains', 'activity_types', 'schedules', 'activities'];
        for (const name of storeNames) {
            await this.clearStore(name);
        }
    }

    async clearStore(storeName) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.clear();
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    // ==========================================
    // 5. 查询数据（本地查询，超快！）
    // ==========================================
    async query(storeName, filters = {}) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.getAll();

            request.onsuccess = () => {
                let results = request.result;

                // 应用过滤条件
                if (filters.id !== undefined) {
                    results = results.filter(r => r.id === filters.id);
                }
                if (filters.event_date) {
                    results = results.filter(r => r.event_date === filters.event_date);
                }
                if (filters.start_date && filters.end_date) {
                    results = results.filter(r =>
                        r.event_date >= filters.start_date && r.event_date <= filters.end_date
                    );
                }
                if (filters.domain_id !== undefined) {
                    results = results.filter(r => r.domain_id === filters.domain_id);
                }
                if (filters.activity_type_id !== undefined) {
                    results = results.filter(r => r.activity_type_id === filters.activity_type_id);
                }
                if (filters.parent_id !== undefined) {
                    results = results.filter(r => r.parent_id === filters.parent_id);
                }

                resolve(results);
            };

            request.onerror = () => {
                console.error(`❌ 查询${storeName}失败:`, request.error);
                reject(request.error);
            };
        });
    }

    // 根据ID获取单条记录
    async getById(storeName, id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.get(id);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    // ==========================================
    // 6. 插入数据（记录更改日志）
    // ==========================================
    async insert(storeName, record) {
        return new Promise((resolve, reject) => {
            // 🔧 移除id字段（如果存在），因为id是auto-increment的keyPath
            const { id, ...recordWithoutId } = record;

            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.add(recordWithoutId);

            request.onsuccess = () => {
                const newId = request.result;
                const newRecord = { ...recordWithoutId, id: newId };

                // 记录更改
                this.logChange('INSERT', storeName, newRecord);
                this.isDirty = true;

                console.log(`💾 本地插入成功: ${storeName} #${newId}`);
                resolve(newRecord);
            };

            request.onerror = () => {
                console.error(`❌ 插入${storeName}失败:`, request.error);
                console.error(`   错误详情:`, request.error.message);
                console.error(`   尝试插入的数据:`, record);
                reject(request.error);
            };
        });
    }

    // ==========================================
    // 7. 更新数据（记录更改日志）
    // ==========================================
    async update(storeName, id, updates) {
        return new Promise(async (resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);

            // 先获取原记录
            const getRequest = store.get(id);

            getRequest.onsuccess = () => {
                const record = getRequest.result;
                if (!record) {
                    reject(new Error(`Record not found: ${storeName} #${id}`));
                    return;
                }

                // 合并更新
                const updatedRecord = { ...record, ...updates };
                const putRequest = store.put(updatedRecord);

                putRequest.onsuccess = () => {
                    // 记录更改
                    this.logChange('UPDATE', storeName, { id, updates });
                    this.isDirty = true;

                    console.log(`💾 本地更新成功: ${storeName} #${id}`);
                    resolve(updatedRecord);
                };

                putRequest.onerror = () => {
                    console.error(`❌ 更新${storeName}失败:`, putRequest.error);
                    reject(putRequest.error);
                };
            };

            getRequest.onerror = () => {
                console.error(`❌ 获取${storeName} #${id}失败:`, getRequest.error);
                reject(getRequest.error);
            };
        });
    }

    // ==========================================
    // 8. 删除数据（记录更改日志）
    // ==========================================
    async delete(storeName, id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.delete(id);

            request.onsuccess = () => {
                // 记录更改
                this.logChange('DELETE', storeName, { id });
                this.isDirty = true;

                console.log(`💾 本地删除成功: ${storeName} #${id}`);
                resolve();
            };

            request.onerror = () => {
                console.error(`❌ 删除${storeName}失败:`, request.error);
                reject(request.error);
            };
        });
    }

    // ==========================================
    // 9. 记录更改日志
    // ==========================================
    logChange(action, table, data) {
        this.changeLog.push({
            action,
            table,
            data,
            timestamp: new Date().toISOString()
        });
        console.log(`📝 记录更改: ${action} ${table}`, data);
    }

    // ==========================================
    // 10. 同步更改到云端
    // ==========================================
    async syncToCloud(apiBaseUrl = '/api') {
        if (!this.isDirty || this.changeLog.length === 0) {
            console.log('✅ 无需同步，本地数据未修改');
            return { success: true, synced: 0 };
        }

        console.log(`🔄 开始同步 ${this.changeLog.length} 条更改到云端...`);
        const startTime = Date.now();

        try {
            // 按操作类型分组
            const inserts = this.changeLog.filter(c => c.action === 'INSERT');
            const updates = this.changeLog.filter(c => c.action === 'UPDATE');
            const deletes = this.changeLog.filter(c => c.action === 'DELETE');

            console.log(`  📊 同步统计: 新增${inserts.length}, 更新${updates.length}, 删除${deletes.length}`);

            // 批量执行同步（顺序：删除 → 插入 → 更新）
            // 注意：插入要在更新前，因为插入后需要用云端ID替换本地ID
            let syncedCount = 0;
            const idMappings = {}; // 存储本地ID到云端ID的映射

            // 1. 先处理删除
            for (const change of deletes) {
                await this.syncDelete(change, apiBaseUrl);
                syncedCount++;
            }

            // 2. 处理新增，并记录ID映射
            for (const change of inserts) {
                const cloudRecord = await this.syncInsert(change, apiBaseUrl);
                syncedCount++;

                // 记录ID映射：本地ID → 云端ID
                if (cloudRecord && cloudRecord.id !== change.data.id) {
                    idMappings[change.table] = idMappings[change.table] || {};
                    idMappings[change.table][change.data.id] = cloudRecord.id;

                    console.log(`  🔄 ID映射: ${change.table} 本地#${change.data.id} → 云端#${cloudRecord.id}`);

                    // 立即更新本地记录的ID
                    await this.updateRecordId(change.table, change.data.id, cloudRecord.id, cloudRecord);
                }
            }

            // 3. 最后处理更新（此时本地ID已经被替换为云端ID）
            for (const change of updates) {
                // 检查是否需要用云端ID替换本地ID
                let targetId = change.data.id;
                if (idMappings[change.table] && idMappings[change.table][targetId]) {
                    targetId = idMappings[change.table][targetId];
                    console.log(`  🔄 更新操作使用云端ID: ${change.table} #${targetId}`);
                }

                await this.syncUpdate(change, apiBaseUrl, targetId);
                syncedCount++;
            }

            // 更新同步状态
            await this.setMetadata('last_sync', new Date().toISOString());
            this.isDirty = false;
            this.changeLog = [];

            const elapsed = Date.now() - startTime;
            console.log(`✅ 同步完成！用时: ${elapsed}ms, 同步记录数: ${syncedCount}`);

            return { success: true, synced: syncedCount, elapsed };

        } catch (error) {
            console.error('❌ 同步失败:', error);
            alert(`数据同步失败: ${error.message}\n\n更改已保存在本地，下次启动时会自动重试。`);
            return { success: false, error: error.message };
        }
    }

    async syncInsert(change, apiBaseUrl) {
        const endpoint = this.getAPIEndpoint(change.table);

        // 移除本地ID，让云端生成新的ID
        const { id, ...dataWithoutId } = change.data;

        const response = await fetch(`${apiBaseUrl}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dataWithoutId)
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Insert failed: ${response.status} - ${errorText}`);
        }

        const cloudRecord = await response.json();
        console.log(`  ✓ 云端新增: ${change.table} 本地#${id} → 云端#${cloudRecord.id}`);

        return cloudRecord; // 返回云端生成的记录（包含云端ID）
    }

    async syncUpdate(change, apiBaseUrl, targetId = null) {
        const endpoint = this.getAPIEndpoint(change.table);
        const id = targetId || change.data.id; // 使用传入的ID或原始ID

        const response = await fetch(`${apiBaseUrl}${endpoint}/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(change.data.updates)
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Update failed: ${response.status} - ${errorText}`);
        }

        console.log(`  ✓ 云端更新: ${change.table} #${id}`);
    }

    async syncDelete(change, apiBaseUrl) {
        const endpoint = this.getAPIEndpoint(change.table);
        const response = await fetch(`${apiBaseUrl}${endpoint}/${change.data.id}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Delete failed: ${response.status} - ${errorText}`);
        }

        console.log(`  ✓ 云端删除: ${change.table} #${change.data.id}`);
    }

    getAPIEndpoint(tableName) {
        const endpoints = {
            'scheduled_events': '/events',
            'domains': '/domains',
            'activity_types': '/activity-types',
            'schedules': '/schedules',
            'activities': '/activities'
        };
        return endpoints[tableName] || `/${tableName}`;
    }

    // ==========================================
    // 11. 更新记录ID（用于同步后替换本地ID为云端ID）
    // ==========================================
    async updateRecordId(storeName, oldId, newId, newRecord) {
        return new Promise(async (resolve, reject) => {
            try {
                const transaction = this.db.transaction([storeName], 'readwrite');
                const store = transaction.objectStore(storeName);

                // 删除旧记录
                const deleteRequest = store.delete(oldId);

                deleteRequest.onsuccess = () => {
                    // 插入带新ID的记录
                    const putRequest = store.put(newRecord);

                    putRequest.onsuccess = () => {
                        console.log(`  🔄 本地ID已更新: ${storeName} #${oldId} → #${newId}`);
                        resolve();
                    };

                    putRequest.onerror = () => {
                        console.error(`❌ 更新记录ID失败 (put):`, putRequest.error);
                        reject(putRequest.error);
                    };
                };

                deleteRequest.onerror = () => {
                    console.error(`❌ 更新记录ID失败 (delete):`, deleteRequest.error);
                    reject(deleteRequest.error);
                };
            } catch (error) {
                console.error(`❌ updateRecordId异常:`, error);
                reject(error);
            }
        });
    }

    // ==========================================
    // 12. 元数据管理
    // ==========================================
    async setMetadata(key, value) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['_metadata'], 'readwrite');
            const store = transaction.objectStore('_metadata');
            const request = store.put({ key, value });
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    async getMetadata(key) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['_metadata'], 'readonly');
            const store = transaction.objectStore('_metadata');
            const request = store.get(key);
            request.onsuccess = () => resolve(request.result?.value);
            request.onerror = () => reject(request.error);
        });
    }

    // ==========================================
    // 12. 工具方法
    // ==========================================

    // 获取同步状态
    getSyncStatus() {
        return {
            isDirty: this.isDirty,
            changeCount: this.changeLog.length,
            hasChanges: this.isDirty && this.changeLog.length > 0
        };
    }

    // 强制标记为脏数据（用于手动触发同步）
    markDirty() {
        this.isDirty = true;
    }

    // 清空更改日志（慎用！）
    clearChangeLog() {
        this.changeLog = [];
        this.isDirty = false;
        console.warn('⚠️ 更改日志已清空');
    }
}

// 导出供全局使用
if (typeof window !== 'undefined') {
    window.LocalDBManager = LocalDBManager;
}
