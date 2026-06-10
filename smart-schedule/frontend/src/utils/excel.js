import * as XLSX from 'xlsx'

export function exportToExcel(data, columns, filename = '导出数据') {
  const header = columns.map(col => col.label)
  const rows = data.map(row =>
    columns.map(col => {
      if (col.formatter) return col.formatter(row)
      return row[col.prop] ?? ''
    })
  )
  const wsData = [header, ...rows]
  const ws = XLSX.utils.aoa_to_sheet(wsData)

  const colWidths = columns.map(col => ({
    wch: Math.max(col.label.length * 2, 12)
  }))
  ws['!cols'] = colWidths

  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Sheet1')
  XLSX.writeFile(wb, `${filename}.xlsx`)
}

export function importFromExcel(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target.result)
        const workbook = XLSX.read(data, { type: 'array' })
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
        const jsonData = XLSX.utils.sheet_to_json(firstSheet, { header: 1 })
        if (jsonData.length < 2) {
          reject(new Error('Excel文件为空或格式不正确'))
          return
        }
        const headers = jsonData[0]
        const rows = jsonData.slice(1).filter(row => row.some(cell => cell !== undefined && cell !== ''))
        resolve({ headers, rows })
      } catch (error) {
        reject(error)
      }
    }
    reader.onerror = () => reject(new Error('文件读取失败'))
    reader.readAsArrayBuffer(file)
  })
}

export function exportTimetableToExcel(timetableData, days, periods, filename = '课表') {
  const wsData = [['', ...days]]
  periods.forEach((period, pIndex) => {
    const row = [period]
    days.forEach((_, dIndex) => {
      const cell = timetableData[pIndex]?.[dIndex]
      if (cell) {
        row.push(`${cell.subject || ''}${cell.teacher ? '(' + cell.teacher + ')' : ''}`)
      } else {
        row.push('')
      }
    })
    wsData.push(row)
  })

  const ws = XLSX.utils.aoa_to_sheet(wsData)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '课表')
  XLSX.writeFile(wb, `${filename}.xlsx`)
}

export function downloadTemplate(columns, filename = '导入模板') {
  const header = columns.map(col => col.label)
  const wsData = [header]
  const ws = XLSX.utils.aoa_to_sheet(wsData)
  ws['!cols'] = columns.map(col => ({ wch: Math.max(col.label.length * 2, 15) }))
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Sheet1')
  XLSX.writeFile(wb, `${filename}.xlsx`)
}
