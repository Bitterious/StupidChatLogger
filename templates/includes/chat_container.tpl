<div class="table_container">
    <table>
        <tr>
            <th>index</th>
            <th>flavor</th>
            <th>user</th>
            <th>content</th>
            <th>timestamp</th>
            <th>server</th>
            <th>map</th>
        </tr>
        <%for data in commits:
            id = data["user_id"]
            index = data["index"]
            name = data["name"]
            url = data["url"]
            avatar = data["avatar"]
            content = data["content"]
            time = data["time"]
            time_og = data["time_og"]
            server = data["server"]
            server_ip = data["server_ip"]
            map = data["map"]
            flavor = ""
            if data["is_dead"] == 1:
                flavor += "*DEAD*"
            end
            if data["is_team"] == 1:
                flavor += "(TEAM)"
            end
            if data["spectator"] == 1:
                flavor = "*SPEC*"
            end
            %>
            <tr>
                <td class="cell_border"><b>{{index}}</b></td>
                <td class="cell_border">{{flavor}}</td>
                <td class="cell_border"><img src="{{avatar}}" class="pfp  pfp_round">
                    <a href="/u/{{id}}/1" class="profilelink" title="{{id}}">{{name}}</a>
                </td>
                <td class="horizontal_overflow cell_border">{{content}}</td>
                <td class="cell_border" title="{{time_og}}">{{time}}</td>
                <td class="cell_border" title="{{server}}">{{server_ip}}</td>
                <td class="cell_border">{{map}}</td>
            </tr>
        % end
    </table>
</div>