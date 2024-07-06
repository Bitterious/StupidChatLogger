steamid64ident = 76561197960265728
def usteamid_to_commid(usteamid):
	for ch in ['[', ']']:
		if ch in usteamid:
			usteamid = usteamid.replace(ch, '')
	usteamid_split = usteamid.split(':')
	commid = int(usteamid_split[2]) + steamid64ident
	return commid
def commid_to_usteamid(commid):
	usteamid = []
	usteamid.append('[U:1:')
	steamidacct = int(commid) - steamid64ident
	usteamid.append(str(steamidacct) + ']')
	return ''.join(usteamid)