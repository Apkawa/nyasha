function CornersInit() {
	var corners = getElementsByClass('corners');
	for (i = 0; i < corners.length; i++) {
		corners[i].innerHTML += '<em class="tl"></em><em class="tr"></em><em class="bl"></em><em class="br"></em>';
	}
}

function getElementsByClass(searchClass,node,tag) {
	var classElements = new Array();
	if ( node == null )	node = document;
	if ( tag == null ) tag = '*';
	var els = node.getElementsByTagName(tag);
	var elsLen = els.length;
	var pattern = new RegExp("(^|\\s)"+searchClass+"(\\s|$)");
	for (i = 0, j = 0; i < elsLen; i++) {
		if (pattern.test(els[i].className) ) {
			classElements[j] = els[i];
			j++;
		}
	}
	return classElements;
}