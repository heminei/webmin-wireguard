// Minimal canvas line chart for RX/TX traffic buckets
function wgChart(id, url, labels) {
	var canvas = document.getElementById(id);
	var ctx = canvas.getContext('2d');

	function fmt(b) {
		var u = ['B', 'kB', 'MB', 'GB', 'TB'], i = 0;
		while (b >= 1024 && i < u.length - 1) { b /= 1024; i++; }
		return (i ? b.toFixed(1) : b) + ' ' + u[i];
	}
	function fmtTime(t, span) {
		var d = new Date(t * 1000);
		var hm = ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2);
		return span > 86400 ? (d.getMonth() + 1) + '/' + d.getDate() + ' ' + hm : hm;
	}
	function draw(data) {
		var w = canvas.width, h = canvas.height;
		var l = 70, r = 10, t = 25, b = 30;
		ctx.clearRect(0, 0, w, h);
		ctx.font = '12px sans-serif';
		var n = data.rx.length, max = 1, total = 0;
		for (var i = 0; i < n; i++) {
			max = Math.max(max, data.rx[i], data.tx[i]);
			total += data.rx[i] + data.tx[i];
		}
		if (!total) {
			ctx.fillStyle = '#666';
			ctx.fillText(labels.empty, l + 10, h / 2);
			return;
		}
		ctx.strokeStyle = '#ddd';
		ctx.fillStyle = '#444';
		for (var g = 0; g <= 4; g++) {
			var y = t + (h - t - b) * g / 4;
			ctx.beginPath(); ctx.moveTo(l, y); ctx.lineTo(w - r, y); ctx.stroke();
			ctx.fillText(fmt(max * (4 - g) / 4), 5, y + 4);
		}
		var span = data.step * n;
		for (var x = 0; x <= 4; x++) {
			var px = l + (w - l - r) * x / 4;
			ctx.fillText(fmtTime(data.start + span * x / 4, span), px - 15, h - 10);
		}
		function line(vals, color) {
			ctx.strokeStyle = color;
			ctx.lineWidth = 2;
			ctx.beginPath();
			for (var i = 0; i < n; i++) {
				var px = l + (w - l - r) * (i + 0.5) / n;
				var py = h - b - (h - t - b) * vals[i] / max;
				if (i) ctx.lineTo(px, py); else ctx.moveTo(px, py);
			}
			ctx.stroke();
		}
		line(data.rx, '#2a7de1');
		line(data.tx, '#e1802a');
		ctx.fillStyle = '#2a7de1'; ctx.fillText('\u25A0 ' + labels.rx, l + 10, 15);
		ctx.fillStyle = '#e1802a'; ctx.fillText('\u25A0 ' + labels.tx, l + 120, 15);
	}

	var xhr = new XMLHttpRequest();
	xhr.open('GET', url);
	xhr.onload = function() {
		try { draw(JSON.parse(xhr.responseText)); } catch (e) { draw({ rx: [], tx: [], start: 0, step: 0 }); }
	};
	xhr.send();
}
