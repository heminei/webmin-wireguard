// Polls live peer counters and updates the peer table in place
function wgLive(iface, labels) {
	function fill(cls, key, data) {
		var els = document.getElementsByClassName(cls);
		for (var i = 0; i < els.length; i++) {
			var p = data.peers[els[i].getAttribute('data-pub')];
			if (p) els[i].textContent = p[key];
		}
	}
	function tick() {
		var xhr = new XMLHttpRequest();
		xhr.open('GET', 'stats_data.cgi?mode=live&iface=' + encodeURIComponent(iface));
		xhr.onload = function() {
			var data;
			try { data = JSON.parse(xhr.responseText); } catch (e) { return; }
			if (!data.peers) return;
			fill('wg-ep', 'endpoint', data);
			fill('wg-hs', 'hs_text', data);
			fill('wg-rx', 'rx_text', data);
			fill('wg-tx', 'tx_text', data);
			var st = document.getElementsByClassName('wg-st');
			for (var i = 0; i < st.length; i++) {
				var p = data.peers[st[i].getAttribute('data-pub')];
				if (!p || st[i].getAttribute('data-dis')) continue;
				st[i].textContent = p.online ? labels.online : labels.offline;
				st[i].style.color = p.online ? '#00aa00' : '';
			}
		};
		xhr.send();
	}
	setInterval(tick, 5000);
}
