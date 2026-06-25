import request from './request'

export const dailyReportApi = (date) => request.get('/reports/daily', { params: { date } })
export const weeklyReportApi = (start_date) => request.get('/reports/weekly', { params: { start_date } })
export const monthlyReportApi = (year, month) => request.get('/reports/monthly', { params: { year, month } })
export const summaryApi = () => request.get('/reports/summary')
