// chart-handler.js
let appliances = [];
const appliancesUl = document.getElementById('appliances_ul');
const addBtn = document.getElementById('add_appliance');
const predictBtn = document.getElementById('predict_btn');
const predText = document.getElementById('prediction_text');

addBtn.onclick = () => {
  const name = document.getElementById('ap_name').value || 'Appliance';
  const power = parseFloat(document.getElementById('ap_power').value) || 0;
  const hours = parseFloat(document.getElementById('ap_hours').value) || 0;
  const days = parseInt(document.getElementById('days').value) || 30;
  appliances.push({name, power_w: power, hours_per_day: hours, days});
  renderAppliances();
};

function renderAppliances(){
  appliancesUl.innerHTML = '';
  appliances.forEach((a,i)=> {
    const li = document.createElement('li');
    li.textContent = `${a.name}: ${a.power_w}W, ${a.hours_per_day} hrs/day, ${a.days} days`;
    const rem = document.createElement('button');
    rem.textContent = 'remove';
    rem.onclick = ()=> { appliances.splice(i,1); renderAppliances(); }
    li.appendChild(rem);
    appliancesUl.appendChild(li);
  })
}

predictBtn.onclick = async () => {
  const existing_kwh = parseFloat(document.getElementById('existing_kwh').value) || 0;
  const rate = parseFloat(document.getElementById('rate').value) || 8;
  const days_in_month = parseInt(document.getElementById('days').value) || 30;
  const payload = { existing_kwh, rate, appliances, days_in_month };
  const res = await fetch('/api/predict', {
    method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)
  });
  const data = await res.json();
  if(data.status === 'ok'){
    predText.innerHTML = `
      Predicted total kWh: <b>${data.predicted_total_kwh}</b> kWh<br>
      Predicted bill: <b>₹${data.predicted_bill}</b><br>
      Extra cost from appliances: <b>₹${data.extra_cost}</b>
    `;
    // show detailed appliance impacts:
    if(data.appliance_impacts && data.appliance_impacts.length){
      predText.innerHTML += '<br><b>Appliance impacts:</b><ul>' +
        data.appliance_impacts.map(a=>`<li>${a.name}: ${a.kwh} kWh → ₹${a.cost}</li>`).join('') +
        '</ul>';
    }
    updateBarChart(existing_kwh, data.predicted_total_kwh);
  } else {
    predText.textContent = 'Error: ' + data.message;
  }
}

// charts
let lineChartCtx = document.getElementById('lineChart').getContext('2d');
let barChartCtx = document.getElementById('barChart').getContext('2d');
let lineChart, barChart;

// load monthly data
fetch('/api/data').then(r=>r.json()).then(res=>{
  if(res.status==='ok'){
    const recs = res.data;
    const labels = recs.map(r=> r.month);
    const total = recs.map(r=> r.total_kwh_est);
    const a = recs.map(r=> r.zone_A_kwh);
    const b = recs.map(r=> r.zone_B_kwh);
    const c = recs.map(r=> r.zone_C_kwh);

    lineChart = new Chart(lineChartCtx, {
      type:'line',
      data:{
        labels,
        datasets:[
          {label:'Zone A kWh', data:a, fill:false},
          {label:'Zone B kWh', data:b, fill:false},
          {label:'Zone C kWh', data:c, fill:false},
          {label:'Total kWh', data:total, fill:false}
        ]
      }
    });

    barChart = new Chart(barChartCtx, {
      type:'bar',
      data:{
        labels:['Current total','With new appliance'],
        datasets:[{label:'kWh', data:[total[total.length-1], total[total.length-1]]}]
      }
    });
  }
});

function updateBarChart(curr, predicted){
  if(barChart){
    barChart.data.datasets[0].data = [curr, predicted];
    barChart.update();
  }
}
