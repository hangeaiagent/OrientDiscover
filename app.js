// 全局变量
let currentPosition = null;
let currentHeading = 0;
let settings = {
    segmentDistance: 100,
    timeMode: 'present',
    speed: 120
};

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    console.log('初始化方向探索应用...');
    
    // 检查浏览器支持
    if (!checkBrowserSupport()) {
        showError('您的浏览器不支持所需功能，请使用现代浏览器访问');
        return;
    }
    
    // 请求权限并获取位置
    await requestPermissions();
    
    // 初始化传感器
    initializeCompass();
    
    // 获取初始位置
    refreshLocation();
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
    
    if (compassNeedle) {
        compassNeedle.style.transform = `translateX(-50%) rotate(${heading}deg)`;
    }
    
    if (compassDirection) {
        compassDirection.textContent = `${Math.round(heading)}°`;
    }
}

function refreshLocation() {
    const locationElement = document.getElementById('currentLocation');
    locationElement.textContent = '获取中...';
    
    if (!navigator.geolocation) {
        showError('浏览器不支持地理位置功能');
        return;
    }
    
    const options = {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000
    };
    
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
        accuracy: position.coords.accuracy
    };
    
    console.log('获取到位置:', currentPosition);
    
    // 更新位置显示
    try {
        const locationName = await getLocationName(currentPosition.latitude, currentPosition.longitude);
        document.getElementById('currentLocation').textContent = locationName;
    } catch (error) {
        document.getElementById('currentLocation').textContent = 
            `${currentPosition.latitude.toFixed(4)}, ${currentPosition.longitude.toFixed(4)}`;
    }
    
    // 启用探索按钮
    document.getElementById('exploreBtn').disabled = false;
}

function handleLocationError(error) {
    let errorMessage = '无法获取位置信息';
    
    switch(error.code) {
        case error.PERMISSION_DENIED:
            errorMessage = '用户拒绝了地理位置请求';
            break;
        case error.POSITION_UNAVAILABLE:
            errorMessage = '位置信息不可用';
            break;
        case error.TIMEOUT:
            errorMessage = '获取位置超时';
            break;
    }
    
    console.error('位置获取错误:', errorMessage);
    showError(errorMessage);
    document.getElementById('currentLocation').textContent = '获取失败';
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
    if (!currentPosition) {
        showError('请先获取当前位置');
        return;
    }
    
    if (currentHeading === null || currentHeading === undefined) {
        showError('请确保设备支持方向检测');
        return;
    }
    
    // 显示加载状态
    showLoading(true);
    document.getElementById('exploreBtn').disabled = true;
    
    try {
        // 调用后端API计算路径
        const response = await fetch('http://localhost:8000/api/explore', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                latitude: currentPosition.latitude,
                longitude: currentPosition.longitude,
                heading: currentHeading,
                segment_distance: settings.segmentDistance,
                time_mode: settings.timeMode,
                speed: settings.speed
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayPlaces(data.places);
        
    } catch (error) {
        console.error('探索请求失败:', error);
        showError('探索请求失败，请检查网络连接或稍后重试');
    } finally {
        showLoading(false);
        document.getElementById('exploreBtn').disabled = false;
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
            <div class="place-coordinates">
                📍 ${place.latitude.toFixed(4)}, ${place.longitude.toFixed(4)}
            </div>
            <p class="place-description">${place.description}</p>
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
    
    console.log('设置已更新:', settings);
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

// 调试功能：模拟方向（用于桌面测试）
function simulateHeading(degrees) {
    currentHeading = degrees;
    updateCompassDisplay(degrees);
    console.log(`模拟方向设置为: ${degrees}°`);
}

// 在控制台中暴露调试函数
window.simulateHeading = simulateHeading;
window.debugInfo = () => {
    console.log('当前位置:', currentPosition);
    console.log('当前方向:', currentHeading);
    console.log('当前设置:', settings);
};