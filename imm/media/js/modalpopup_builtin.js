/*** Copy Right Information ***
  * Please do not remove following information.
  * Modal Popup v1.0
  * Author: John J Kim
  * Email: john@frontendframework.com
  * URL: www.FrontEndFramework.com
  * 
  * You are welcome to modify the codes as long as you include this copyright information.
 *****************************/

//With the window size & the element size functions built-in
ModalPopup = function (elem,options) {
	//option default settings
	options = options || {};
	var HasBackground = (options.HasBackground!=null)?options.HasBackground:true;
	var BackgroundColor = options.BackgroundColor || '#0f0f0f';
	var BackgroundOpacity = options.BackgroundOpacity || 60; // 1-100
	BackgroundOpacity = (BackgroundOpacity > 0) ? BackgroundOpacity : 1;
	var BackgroundOnClick = options.BackgroundOnClick || function(){};
	var BackgroundCursorStyle = options.BackgroundCursorStyle || "default";
	var Zindex = options.Zindex || 90000;
	var AddLeft = options.AddLeft || 0; //in px
	var AddTop = options.AddTop || 0; //in px

	function _Convert(val) {
		if (!val) {return;}
		val = val.replace("px","");
		if (isNaN(val)) {return 0;}
		return parseInt(val);
	}
	var popup = document.getElementById(elem);
	if (!popup) {return;}
	//set the popup layer styles
	var winW = (document.layers||(document.getElementById&&!document.all)) ? window.outerWidth : (document.all ? document.body.clientWidth : 0);
	var winH = window.innerHeight ? window.innerHeight :(document.getBoxObjectFor ? Math.min(document.documentElement.clientHeight, document.body.clientHeight) : ((document.documentElement.clientHeight != 0) ? document.documentElement.clientHeight : (document.body ? document.body.clientHeight : 0)));
	//display the popup layer
	
	if (HasBackground) {		
		if (!ModalPopup._BackgroundDiv) {
			ModalPopup._BackgroundDiv = document.createElement('div');
			ModalPopup._BackgroundDiv.style.display = "none";
			ModalPopup._BackgroundDiv.style.width = "100%";
			ModalPopup._BackgroundDiv.style.position = "absolute";
			ModalPopup._BackgroundDiv.style.top = "0px";
			ModalPopup._BackgroundDiv.style.left = "0px";
			document.body.appendChild(ModalPopup._BackgroundDiv);
		}
		ModalPopup._BackgroundDiv.onclick =  BackgroundOnClick;
		ModalPopup._BackgroundDiv.style.background = BackgroundColor;	
//		ModalPopup._BackgroundDiv.style.height = document.all ? Math.max(Math.max(document.documentElement.offsetHeight, document.documentElement.scrollHeight), Math.max(document.body.offsetHeight, document.body.scrollHeight)) : (document.body ? document.body.scrollHeight : ((document.documentElement.scrollHeight != 0) ? document.documentElement.scrollHeight : 0)) + "px";

		ModalPopup._BackgroundDiv.style.height = "100%";
		ModalPopup._BackgroundDiv.style.filter = "progid:DXImageTransform.Microsoft.Alpha(opacity=" + BackgroundOpacity +")";
		ModalPopup._BackgroundDiv.style.MozOpacity = BackgroundOpacity / 100;
		ModalPopup._BackgroundDiv.style.opacity = BackgroundOpacity / 100;
		ModalPopup._BackgroundDiv.style.zIndex = Zindex;
		ModalPopup._BackgroundDiv.style.cursor = BackgroundCursorStyle;

		//Display the background
		ModalPopup._BackgroundDiv.style.display = "";
	}

	popup.style.display = "block";
	popup.style.visibility = "visible";
	var currentStyle;
	if (popup.currentStyle)	{ 
		currentStyle = popup.currentStyle; 
	}
	else if (window.getComputedStyle) {
		currentStyle = document.defaultView.getComputedStyle(popup, null);
	} else {
		currentStyle = popup.style;
	}

	var elemW = popup.offsetWidth -
		_Convert(currentStyle.marginLeft) -
		_Convert(currentStyle.marginRight) -
		_Convert(currentStyle.borderLeftWidth) -
		_Convert(currentStyle.borderRightWidth);

	var elemH = popup.offsetHeight -
		_Convert(currentStyle.marginTop) -
		_Convert(currentStyle.marginBottom) -
		_Convert(currentStyle.borderTopWidth) -
		_Convert(currentStyle.borderBottomWidth);

	popup.style.position = "fixed";
	popup.style.left = (winW/2 - elemW/2 + AddLeft) + "px";
	popup.style.top = (winH/2 - elemH/2 + AddTop - 10) + "px";
	popup.style.zIndex = Zindex + 1;

}

ModalPopup.Close = function(id) {
	if (id) {
		document.getElementById(id).style.display = "none";
		document.getElementById(id).style.visibility = "hidden";
	} 
	if  (ModalPopup._BackgroundDiv) {
		ModalPopup._BackgroundDiv.style.display = "none";
	}
}
