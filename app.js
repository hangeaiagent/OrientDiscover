// 全局变量
let currentPosition = null;
let currentHeading = 0;
let settings = {
    segmentDistance: 10,
    timeMode: 'present',
    speed: 120,
    dataSource: 'real'  // 只使用真实数据
};

// 日志系统
class Logger {
    constructor() {
        this.logs = [];
        this.maxLogs = 100;
    }
    
    log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = {
            timestamp,
            message,
            type,
            id: Date.now()
        };
        
        this.logs.unshift(logEntry);
        if (this.logs.length > this.maxLogs) {
            this.logs.pop();
        }
        
        this.displayLog(logEntry);
        console.log(`[${timestamp}] ${type.toUpperCase()}: ${message}`);
    }
    
    info(message) { this.log(message, 'info'); }
    success(message) { this.log(message, 'success'); }
    warning(message) { this.log(message, 'warning'); }
    error(message) { this.log(message, 'error'); }
    
    displayLog(logEntry) {
        const container = document.getElementById('logContainer');
        if (!container) return;
        
        const logElement = document.createElement('div');
        logElement.className = `log-entry ${logEntry.type}`;
        logElement.innerHTML = `
            <span class="log-timestamp">[${logEntry.timestamp}]</span>
            <span class="log-message">${logEntry.message}</span>
        `;
        
        container.insertBefore(logElement, container.firstChild);
        
        // 限制显示的日志数量
        const entries = container.querySelectorAll('.log-entry');
        if (entries.length > 50) {
            entries[entries.length - 1].remove();
        }
    }
    
    clear() {
        this.logs = [];
        const container = document.getElementById('logContainer');
        if (container) {
            container.innerHTML = '';
        }
        console.clear();
    }
}

const logger = new Logger();

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    logger.info('🧭 方向探索派对应用启动');
    logger.info('正在初始化应用组件...');
    
    // 检查浏览器支持
    if (!checkBrowserSupport()) {
        const errorMsg = '您的浏览器不支持所需功能，请使用现代浏览器访问';
        logger.error(errorMsg);
        showError(errorMsg);
        return;
    }
    
    logger.success('浏览器兼容性检查通过');
    
    // 请求权限并获取位置
    await requestPermissions();
    
    // 初始化传感器
    initializeCompass();
    
    // 获取初始位置
    refreshLocation();
    
    logger.success('应用初始化完成');
}

function checkBrowserSupport() {
    return 'geolocation' in navigator && 
           'DeviceOrientationEvent' in window &&
           typeof fetch !== 'undefined';
}

async function requestPermissions() {
    try {
        // 请求地理位置权限
        if ('permissions' in navigator) {
            const geoPermission = await navigator.permissions.query({name: 'geolocation'});
            console.log('地理位置权限状态:', geoPermission.state);
        }
        
        // 请求设备方向权限 (iOS 13+)
        if (typeof DeviceOrientationEvent.requestPermission === 'function') {
            const permission = await DeviceOrientationEvent.requestPermission();
            if (permission !== 'granted') {
                showError('需要设备方向权限才能使用指南针功能');
            }
        }
    } catch (error) {
        console.error('权限请求失败:', error);
    }
}

function initializeCompass() {
    // 监听设备方向变化
    if (window.DeviceOrientationEvent) {
        window.addEventListener('deviceorientation', handleOrientation, true);
        window.addEventListener('deviceorientationabsolute', handleOrientation, true);
    } else {
        console.warn('设备不支持方向检测');
        showError('设备不支持方向检测功能');
    }
}

function handleOrientation(event) {
    // 获取指南针方向
    let heading = event.alpha;
    
    // iOS Safari 使用 webkitCompassHeading
    if (event.webkitCompassHeading) {
        heading = event.webkitCompassHeading;
    }
    
    if (heading !== null) {
        // 标准化角度 (0-360)
        heading = (360 - heading) % 360;
        currentHeading = heading;
        updateCompassDisplay(heading);
    }
}

function updateCompassDisplay(heading) {
    const compassNeedle = document.getElementById('compassNeedle');
    const compassDirection = document.getElementById('compassDirection');
    const directionText = document.getElementById('directionText');
    
    if (compassNeedle) {
        compassNeedle.style.transform = `translateX(-50%) rotate(${heading}deg)`;
    }
    
    if (compassDirection) {
        compassDirection.textContent = `${Math.round(heading)}°`;
    }
    
    if (directionText) {
        directionText.textContent = getDirectionText(heading);
    }
    
    logger.info(`方向更新: ${Math.round(heading)}° (${getDirectionText(heading)})`);
}

function getDirectionText(heading) {
    const directions = [
        { name: '北', min: 0, max: 22.5 },
        { name: '东北', min: 22.5, max: 67.5 },
        { name: '东', min: 67.5, max: 112.5 },
        { name: '东南', min: 112.5, max: 157.5 },
        { name: '南', min: 157.5, max: 202.5 },
        { name: '西南', min: 202.5, max: 247.5 },
        { name: '西', min: 247.5, max: 292.5 },
        { name: '西北', min: 292.5, max: 337.5 },
        { name: '北', min: 337.5, max: 360 }
    ];
    
    for (const dir of directions) {
        if (heading >= dir.min && heading < dir.max) {
            return dir.name;
        }
    }
    return '北';
}

function refreshLocation() {
    logger.info('开始获取位置信息...');
    
    const locationElement = document.getElementById('currentLocation');
    const coordinatesElement = document.getElementById('coordinates');
    const accuracyElement = document.getElementById('accuracy');
    
    locationElement.textContent = '获取中...';
    coordinatesElement.textContent = '获取中...';
    accuracyElement.textContent = '获取中...';
    
    if (!navigator.geolocation) {
        const errorMsg = '浏览器不支持地理位置功能';
        logger.error(errorMsg);
        showError(errorMsg);
        return;
    }
    
    const options = {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 30000
    };
    
    logger.info(`位置获取选项: 高精度=${options.enableHighAccuracy}, 超时=${options.timeout}ms`);
    
    navigator.geolocation.getCurrentPosition(
        handleLocationSuccess,
        handleLocationError,
        options
    );
}

async function handleLocationSuccess(position) {
    currentPosition = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        altitude: position.coords.altitude,
        altitudeAccuracy: position.coords.altitudeAccuracy,
        heading: position.coords.heading,
        speed: position.coords.speed,
        timestamp: position.timestamp
    };
    
    logger.success(`位置获取成功: ${currentPosition.latitude.toFixed(6)}, ${currentPosition.longitude.toFixed(6)}`);
    logger.info(`位置精度: ${Math.round(currentPosition.accuracy)}米`);
    
    // 更新坐标显示
    document.getElementById('coordinates').textContent = 
        `${currentPosition.latitude.toFixed(6)}, ${currentPosition.longitude.toFixed(6)}`;
    
    // 更新精度显示
    document.getElementById('accuracy').textContent = `±${Math.round(currentPosition.accuracy)}m`;
    
    // 更新位置显示
    try {
        logger.info('正在获取地址信息...');
        const locationName = await getLocationName(currentPosition.latitude, currentPosition.longitude);
        document.getElementById('currentLocation').textContent = locationName;
        logger.success(`地址获取成功: ${locationName}`);
    } catch (error) {
        logger.warning(`地址获取失败: ${error.message}`);
        document.getElementById('currentLocation').textContent = 
            `${currentPosition.latitude.toFixed(4)}, ${currentPosition.longitude.toFixed(4)}`;
    }
    
    // 记录额外的位置信息
    if (currentPosition.altitude !== null) {
        logger.info(`海拔高度: ${Math.round(currentPosition.altitude)}米`);
    }
    if (currentPosition.speed !== null) {
        logger.info(`移动速度: ${Math.round(currentPosition.speed * 3.6)}km/h`);
    }
    
    // 启用探索按钮
    document.getElementById('exploreBtn').disabled = false;
    logger.success('位置信息更新完成，探索功能已启用');
}

function handleLocationError(error) {
    let errorMessage = '无法获取位置信息';
    let errorDetails = '';
    
    switch(error.code) {
        case error.PERMISSION_DENIED:
            errorMessage = '用户拒绝了地理位置请求';
            errorDetails = '请在浏览器设置中允许位置访问权限';
            break;
        case error.POSITION_UNAVAILABLE:
            errorMessage = '位置信息不可用';
            errorDetails = '设备无法确定位置，请检查GPS或网络连接';
            break;
        case error.TIMEOUT:
            errorMessage = '获取位置超时';
            errorDetails = '位置获取时间过长，请重试';
            break;
        default:
            errorMessage = '未知的位置获取错误';
            errorDetails = `错误代码: ${error.code}`;
    }
    
    logger.error(`${errorMessage}: ${errorDetails}`);
    logger.error(`错误详情: ${error.message}`);
    
    // 更新UI显示
    document.getElementById('currentLocation').textContent = '获取失败';
    document.getElementById('coordinates').textContent = '无法获取';
    document.getElementById('accuracy').textContent = '无法获取';
    
    showError(`${errorMessage}\n${errorDetails}`);
}

async function getLocationName(lat, lng) {
    // 使用反向地理编码获取地点名称
    // 这里使用一个简单的实现，实际项目中可以使用更好的地理编码服务
    try {
        const response = await fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lng}&localityLanguage=zh`);
        const data = await response.json();
        
        if (data.city && data.countryName) {
            return `${data.city}, ${data.countryName}`;
        } else if (data.locality && data.countryName) {
            return `${data.locality}, ${data.countryName}`;
        } else {
            return data.countryName || '未知位置';
        }
    } catch (error) {
        console.error('获取地点名称失败:', error);
        throw error;
    }
}

async function startExploration() {
    logger.info('开始方向探索...');
    
    if (!currentPosition) {
        const errorMsg = '请先获取当前位置';
        logger.error(errorMsg);
        showError(errorMsg);
        return;
    }
    
    if (currentHeading === null || currentHeading === undefined) {
        const errorMsg = '请确保设备支持方向检测';
        logger.error(errorMsg);
        showError(errorMsg);
        return;
    }
    
    // 记录探索参数
    const exploreParams = {
        latitude: currentPosition.latitude,
        longitude: currentPosition.longitude,
        heading: currentHeading,
        segment_distance: settings.segmentDistance,
        time_mode: settings.timeMode,
        speed: settings.speed
    };
    
    logger.info(`探索参数: 位置(${exploreParams.latitude.toFixed(4)}, ${exploreParams.longitude.toFixed(4)})`);
    logger.info(`方向: ${exploreParams.heading}° (${getDirectionText(exploreParams.heading)})`);
    logger.info(`分段距离: ${exploreParams.segment_distance}km, 时间模式: ${exploreParams.time_mode}, 速度: ${exploreParams.speed}km/h`);
    
    // 显示加载状态
    showLoading(true);
    document.getElementById('exploreBtn').disabled = true;
    
    try {
        logger.info('正在向后端发送探索请求...');
        const startTime = Date.now();
        
                // 使用真实数据API端点
        const apiEndpoint = 'http://localhost:8000/api/explore-real';
        logger.info('使用真实数据源');
        
        // 调用后端API计算路径
        const response = await fetch(apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(exploreParams)
        });
        
        const requestTime = Date.now() - startTime;
        logger.info(`API请求耗时: ${requestTime}ms`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        logger.success(`探索完成! 找到 ${data.places.length} 个地点`);
        logger.info(`总距离: ${data.total_distance}km, 计算时间: ${(data.calculation_time * 1000).toFixed(1)}ms`);
        
        displayPlaces(data.places);
        
    } catch (error) {
        logger.error(`探索请求失败: ${error.message}`);
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            showError('无法连接到服务器，请确保后端服务正在运行');
        } else {
            showError(`探索请求失败: ${error.message}`);
        }
    } finally {
        showLoading(false);
        document.getElementById('exploreBtn').disabled = false;
        logger.info('探索操作结束');
    }
}

function displayPlaces(places) {
    const container = document.getElementById('placesContainer');
    container.innerHTML = '';
    
    if (!places || places.length === 0) {
        container.innerHTML = '<div class="error-message">没有找到相关地点信息</div>';
        return;
    }
    
    places.forEach((place, index) => {
        const placeCard = createPlaceCard(place, index);
        container.appendChild(placeCard);
    });
}

function createPlaceCard(place, index) {
    const card = document.createElement('div');
    card.className = 'place-card';
    
    const modeText = {
        'present': '现代',
        'past': '历史',
        'future': '未来'
    }[settings.timeMode] || '现代';
    
    // 格式化价格显示
    const formatPrice = (price) => {
        if (!price) return '暂无信息';
        if (price.includes('免费')) {
            return `<span class="free-price">${price}</span>`;
        }
        return `<span class="price-highlight">${price}</span>`;
    };
    
    card.innerHTML = `
        <img src="${place.image || 'https://via.placeholder.com/400x200?text=暂无图片'}" 
             alt="${place.name}" 
             class="place-image"
             onerror="this.src='https://via.placeholder.com/400x200?text=暂无图片'">
        <div class="place-content">
            <div class="place-header">
                <h3 class="place-name">${place.name}</h3>
                <span class="place-distance">${place.distance}km</span>
            </div>
            
            ${place.category ? `<div class="place-category">🏷️ ${place.category}</div>` : ''}
            
            <div class="place-location-info">
                📍 ${place.latitude.toFixed(4)}°, ${place.longitude.toFixed(4)}°
                ${place.country ? `| ${place.country}` : ''}
                ${place.city ? ` - ${place.city}` : ''}
            </div>
            
            <p class="place-description">${place.description}</p>
            
            <div class="place-details">
                <div class="detail-item">
                    <div class="detail-label">🕒 开放时间</div>
                    <div class="detail-value">${place.opening_hours || '暂无信息'}</div>
                </div>
                
                <div class="detail-item">
                    <div class="detail-label">💰 门票价格</div>
                    <div class="detail-value">${formatPrice(place.ticket_price)}</div>
                </div>
                
                <div class="detail-item">
                    <div class="detail-label">🎫 购票方式</div>
                    <div class="detail-value">${place.booking_method || '暂无信息'}</div>
                </div>
                
                <div class="detail-item">
                    <div class="detail-label">📍 精确坐标</div>
                    <div class="detail-value">${place.latitude.toFixed(6)}, ${place.longitude.toFixed(6)}</div>
                </div>
            </div>
            
            <span class="place-mode">${modeText}模式</span>
        </div>
    `;
    
    return card;
}

function toggleSettings() {
    const panel = document.getElementById('settingsPanel');
    panel.classList.toggle('show');
}

function updateSettings() {
    settings.segmentDistance = parseInt(document.getElementById('segmentDistance').value);
    settings.timeMode = document.getElementById('timeMode').value;
    settings.speed = parseInt(document.getElementById('speed').value);
    
    logger.info(`设置已更新: ${settings.segmentDistance}km, ${settings.timeMode}模式, ${settings.speed}km/h`);
}

function showLoading(show) {
    const loading = document.getElementById('loading');
    loading.style.display = show ? 'block' : 'none';
}

function showError(message) {
    // 移除现有的错误消息
    const existingError = document.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // 创建新的错误消息
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    // 插入到状态区域后面
    const statusSection = document.querySelector('.status-section');
    statusSection.insertAdjacentElement('afterend', errorDiv);
    
    // 5秒后自动移除
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.remove();
        }
    }, 5000);
}

function showSuccess(message) {
    // 移除现有的成功消息
    const existingSuccess = document.querySelector('.success-message');
    if (existingSuccess) {
        existingSuccess.remove();
    }
    
    // 创建新的成功消息
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.textContent = message;
    
    // 插入到状态区域后面
    const statusSection = document.querySelector('.status-section');
    statusSection.insertAdjacentElement('afterend', successDiv);
    
    // 3秒后自动移除
    setTimeout(() => {
        if (successDiv.parentNode) {
            successDiv.remove();
        }
    }, 3000);
}

// 清空日志函数
function clearLogs() {
    logger.clear();
    logger.info('日志已清空');
}

// 调试功能：模拟方向（用于桌面测试）
function simulateHeading(degrees) {
    currentHeading = degrees;
    updateCompassDisplay(degrees);
    logger.info(`模拟方向设置为: ${degrees}° (${getDirectionText(degrees)})`);
}

// 调试信息函数
function debugInfo() {
    logger.info('=== 调试信息 ===');
    logger.info(`当前位置: ${currentPosition ? `${currentPosition.latitude.toFixed(6)}, ${currentPosition.longitude.toFixed(6)}` : '未获取'}`);
    logger.info(`位置精度: ${currentPosition ? `±${Math.round(currentPosition.accuracy)}m` : '未知'}`);
    logger.info(`当前方向: ${currentHeading !== null ? `${Math.round(currentHeading)}° (${getDirectionText(currentHeading)})` : '未检测'}`);
    logger.info(`设置: 分段${settings.segmentDistance}km, ${settings.timeMode}模式, ${settings.speed}km/h`);
    logger.info(`浏览器: ${navigator.userAgent}`);
    logger.info(`屏幕: ${screen.width}x${screen.height}`);
    logger.info('===============');
}

// 获取系统状态
function getSystemStatus() {
    const status = {
        hasPosition: !!currentPosition,
        hasHeading: currentHeading !== null && currentHeading !== undefined,
        geolocationSupported: 'geolocation' in navigator,
        orientationSupported: 'DeviceOrientationEvent' in window,
        isSecureContext: window.isSecureContext,
        userAgent: navigator.userAgent
    };
    
    logger.info('系统状态检查:');
    Object.entries(status).forEach(([key, value]) => {
        const type = value ? 'success' : 'warning';
        logger.log(`${key}: ${value}`, type);
    });
    
    return status;
}

// 在控制台中暴露调试函数
window.simulateHeading = simulateHeading;
window.debugInfo = debugInfo;
window.clearLogs = clearLogs;
window.getSystemStatus = getSystemStatus;
window.logger = logger;