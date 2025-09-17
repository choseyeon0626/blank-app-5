import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import numpy as np
import pandas as pd

# ----- 1. 데이터 준비 -----
# 가상의 전 지구 해수면 상승 데이터 생성 (mm 단위)
latitude = np.arange(-90, 91, 1)
longitude = np.arange(-180, 181, 1)
lon_grid, lat_grid = np.meshgrid(longitude, latitude)
sea_level_data = 100 + 50 * np.cos(np.deg2rad(lat_grid)) + 20 * np.random.rand(len(latitude), len(longitude))
sea_level_data = xr.DataArray(
    sea_level_data,
    coords=[('lat', latitude), ('lon', longitude)],
    name='sea_level_rise_mm'
)

# 에어컨 사용량 데이터 (가상의 데이터)
# 에어컨 보급률 및 사용량 증가에 따라 해수면 상승과 유사한 추세를 보인다는 가정을 반영
years = np.arange(2000, 2025)
ac_usage_data = np.linspace(10, 25, len(years)) + np.random.randn(len(years)) * 1.5
df_ac = pd.DataFrame({
    'Year': years,
    'AC_Usage_Index': ac_usage_data
})

# 해수면 상승 데이터 (가상의 데이터, 추세 반영)
sea_level_increase = np.linspace(0, 104, len(years)) + np.random.randn(len(years)) * 2
df_sea_level = pd.DataFrame({
    'Year': years,
    'Sea_Level_Rise_mm': sea_level_increase
})

# ----- 2. 그래프 그리기 -----
# 1행 2열의 서브플롯을 생성
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8), gridspec_kw={'width_ratios': [1.5, 1]})

# 첫 번째 서브플롯: 전 지구 해수면 상승 지도
ax1 = plt.subplot(1, 2, 1, projection=ccrs.Robinson())
ax1.coastlines()
ax1.add_feature(ccrs.cartopy.feature.LAND, facecolor='lightgray')

c = ax1.pcolormesh(
    sea_level_data['lon'],
    sea_level_data['lat'],
    sea_level_data.values,
    cmap='viridis',
    transform=ccrs.PlateCarree(),
    vmin=sea_level_data.values.min(),
    vmax=sea_level_data.values.max()
)
cbar = fig.colorbar(c, ax=ax1, orientation='horizontal', pad=0.05)
cbar.set_label('2000-2024 해수면 상승량 (mm)')
ax1.set_title("2000-2024 전 지구 해수면 상승")

# 두 번째 서브플롯: 꺾은선 그래프
ax2 = plt.subplot(1, 2, 2)
ax2.plot(df_ac['Year'], df_ac['AC_Usage_Index'], color='red', marker='o', label='에어컨 사용량 (가상 지수)')
ax2.plot(df_sea_level['Year'], df_sea_level['Sea_Level_Rise_mm'], color='blue', marker='s', label='전 지구 해수면 상승 (mm)')

ax2.set_title('연도별 에어컨 사용량과 해수면 상승 비교')
ax2.set_xlabel('연도')
ax2.set_ylabel('값')
ax2.legend()
ax2.grid(True)

plt.tight_layout()  # 서브플롯 간의 간격 조정
plt.show()
