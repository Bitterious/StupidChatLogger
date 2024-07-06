<div class="filtercontainer">
	<form action="/query/search" method="post" class="filtercontainer">
		<select id="type" class="filterlist" style="background-color: darkslategray;" name="type">
			<option value="name">Username</option>
			<option value="user">UserID</option>
			<option value="contains">Message</option>
			<option value="map">Map</option>
			<option value="servers">Servers</option>
			<option value="ip">ServerIP</option>
		</select>
		<input type="text" id="name" name="namebox" class="filterlist size20">
		<input type="submit" value="Search" class="filterlist">
	</form>
</div>