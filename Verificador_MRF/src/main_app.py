# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 4.1.0-0-g733bf3d)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
import wx.adv
import wx.stc

###########################################################################
## Class MainF
###########################################################################

class MainF ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"Validaciones USO", pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.Size( 720,400 ), wx.Size( -1,-1 ) )

		MainS = wx.BoxSizer( wx.HORIZONTAL )

		Sizer0 = wx.BoxSizer( wx.VERTICAL )

		self.main_notebook1 = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.MAGE_panel = wx.Panel( self.main_notebook1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		MAGEmSizer = wx.BoxSizer( wx.HORIZONTAL )

		Param_Sizer = wx.BoxSizer( wx.VERTICAL )

		self.logo_cen1 = wx.StaticBitmap( self.MAGE_panel, wx.ID_ANY, wx.Bitmap( u"D:\\E0139.CENACE\\My Documents\\Mis imágenes\\iconos\\CENACE-logo-completo.png", wx.BITMAP_TYPE_ANY ), wx.DefaultPosition, wx.DefaultSize, 0 )
		Param_Sizer.Add( self.logo_cen1, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

		path_insumosSizer = wx.StaticBoxSizer( wx.StaticBox( self.MAGE_panel, wx.ID_ANY, u"Seleccionar insumos" ), wx.VERTICAL )

		self.MAGE_pathSel = wx.DirPickerCtrl( path_insumosSizer.GetStaticBox(), wx.ID_ANY, u"Seleccinar carpeta de MAGE", u"Seleccionar carpeta", wx.DefaultPosition, wx.DefaultSize, wx.DIRP_DEFAULT_STYLE|wx.DIRP_DIR_MUST_EXIST )
		path_insumosSizer.Add( self.MAGE_pathSel, 0, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		self.bto_preprocesar_archivos = wx.Button( path_insumosSizer.GetStaticBox(), wx.ID_ANY, u"Procesar Archivos", wx.DefaultPosition, wx.DefaultSize, 0 )
		path_insumosSizer.Add( self.bto_preprocesar_archivos, 0, wx.ALL|wx.EXPAND|wx.LEFT, 0 )


		Param_Sizer.Add( path_insumosSizer, 0, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		Ceck_Sizer = wx.StaticBoxSizer( wx.StaticBox( self.MAGE_panel, wx.ID_ANY, u"Lista de Validaciones" ), wx.VERTICAL )

		Ceck_Sizer.SetMinSize( wx.Size( 240,140 ) )
		Val_Sizer = wx.BoxSizer( wx.VERTICAL )

		self.Maestro_checkBox = wx.CheckBox( Ceck_Sizer.GetStaticBox(), wx.ID_ANY, u"Hacer todas las validaciones", wx.DefaultPosition, wx.DefaultSize, 0 )
		Val_Sizer.Add( self.Maestro_checkBox, 0, wx.ALL|wx.EXPAND, 5 )

		List_Sizer = wx.BoxSizer( wx.HORIZONTAL )

		Val_checkBoxListChoices = []
		self.Val_checkBoxList = wx.CheckListBox( Ceck_Sizer.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, Val_checkBoxListChoices, 0 )
		List_Sizer.Add( self.Val_checkBoxList, 1, wx.ALL|wx.EXPAND|wx.LEFT, 0 )

		self.ValDesc_textCtrl = wx.TextCtrl( Ceck_Sizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE|wx.TE_READONLY )
		List_Sizer.Add( self.ValDesc_textCtrl, 1, wx.ALL|wx.EXPAND|wx.LEFT, 0 )


		Val_Sizer.Add( List_Sizer, 5, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		self.bto_verificar_mage = wx.Button( Ceck_Sizer.GetStaticBox(), wx.ID_ANY, u"Realizar validaciones", wx.DefaultPosition, wx.DefaultSize, 0 )
		Val_Sizer.Add( self.bto_verificar_mage, 0, wx.ALL|wx.EXPAND|wx.LEFT, 0 )

		Report_Sizer = wx.BoxSizer( wx.HORIZONTAL )

		self.Export_checkBox = wx.CheckBox( Ceck_Sizer.GetStaticBox(), wx.ID_ANY, u"Exportar reporte", wx.DefaultPosition, wx.DefaultSize, 0 )
		Report_Sizer.Add( self.Export_checkBox, 0, wx.ALL, 5 )

		self.Export_button = wx.Button( Ceck_Sizer.GetStaticBox(), wx.ID_ANY, u"Exportar archivo", wx.DefaultPosition, wx.DefaultSize, 0 )
		Report_Sizer.Add( self.Export_button, 3, wx.ALL|wx.LEFT, 5 )


		Val_Sizer.Add( Report_Sizer, 1, wx.EXPAND, 5 )


		Ceck_Sizer.Add( Val_Sizer, 1, wx.EXPAND, 5 )


		Param_Sizer.Add( Ceck_Sizer, 1, wx.ALL|wx.EXPAND|wx.LEFT, 5 )


		MAGEmSizer.Add( Param_Sizer, 1, wx.EXPAND, 5 )

		Logger_Sizer = wx.BoxSizer( wx.VERTICAL )

		self.mage_log_textCtrl = wx.TextCtrl( self.MAGE_panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL|wx.TE_MULTILINE|wx.TE_READONLY )
		Logger_Sizer.Add( self.mage_log_textCtrl, 1, wx.ALL|wx.EXPAND, 5 )


		MAGEmSizer.Add( Logger_Sizer, 1, wx.EXPAND, 5 )


		self.MAGE_panel.SetSizer( MAGEmSizer )
		self.MAGE_panel.Layout()
		MAGEmSizer.Fit( self.MAGE_panel )
		self.main_notebook1.AddPage( self.MAGE_panel, u"MAGE", False )
		self.XML_panel = wx.Panel( self.main_notebook1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		XMLmSizer1 = wx.BoxSizer( wx.HORIZONTAL )

		Param_Sizer1 = wx.BoxSizer( wx.VERTICAL )

		self.logo_cen2 = wx.StaticBitmap( self.XML_panel, wx.ID_ANY, wx.Bitmap( u"D:\\E0139.CENACE\\My Documents\\Mis imágenes\\iconos\\CENACE-logo-completo.png", wx.BITMAP_TYPE_ANY ), wx.DefaultPosition, wx.DefaultSize, 0 )
		Param_Sizer1.Add( self.logo_cen2, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

		Data_Sizer1 = wx.StaticBoxSizer( wx.StaticBox( self.XML_panel, wx.ID_ANY, u"Seleccionar insumos" ), wx.VERTICAL )

		self.XML_pathSel = wx.DirPickerCtrl( Data_Sizer1.GetStaticBox(), wx.ID_ANY, u"Seleccionar directorio de XML", u"Seleccionar carpeta", wx.DefaultPosition, wx.DefaultSize, wx.DIRP_DEFAULT_STYLE|wx.DIRP_DIR_MUST_EXIST|wx.DIRP_USE_TEXTCTRL )
		Data_Sizer1.Add( self.XML_pathSel, 0, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		self.Data_athSelect1 = wx.DirPickerCtrl( Data_Sizer1.GetStaticBox(), wx.ID_ANY, u"Seleccioanr directorio de insumos", u"Seleccionar carpeta", wx.DefaultPosition, wx.DefaultSize, wx.DIRP_DEFAULT_STYLE|wx.DIRP_DIR_MUST_EXIST )
		Data_Sizer1.Add( self.Data_athSelect1, 0, wx.ALL|wx.EXPAND|wx.LEFT, 5 )


		Param_Sizer1.Add( Data_Sizer1, 0, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		Ceck_Sizer1 = wx.StaticBoxSizer( wx.StaticBox( self.XML_panel, wx.ID_ANY, u"Establecer fecha y hora" ), wx.HORIZONTAL )

		Ceck_Sizer1.SetMinSize( wx.Size( 240,140 ) )
		bSizer38 = wx.BoxSizer( wx.VERTICAL )

		self.start_time_sText = wx.StaticText( Ceck_Sizer1.GetStaticBox(), wx.ID_ANY, u"Hora inicial", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.start_time_sText.Wrap( -1 )

		bSizer38.Add( self.start_time_sText, 0, wx.ALL, 5 )

		self.start_tPicker = wx.adv.TimePickerCtrl( Ceck_Sizer1.GetStaticBox(), wx.ID_ANY, wx.DefaultDateTime, wx.DefaultPosition, wx.DefaultSize, wx.adv.TP_DEFAULT )
		bSizer38.Add( self.start_tPicker, 0, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		self.end_time_sText = wx.StaticText( Ceck_Sizer1.GetStaticBox(), wx.ID_ANY, u"Hora final", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.end_time_sText.Wrap( -1 )

		bSizer38.Add( self.end_time_sText, 0, wx.ALL, 5 )

		self.end_tPicker = wx.adv.TimePickerCtrl( Ceck_Sizer1.GetStaticBox(), wx.ID_ANY, wx.DefaultDateTime, wx.DefaultPosition, wx.DefaultSize, wx.adv.TP_DEFAULT )
		bSizer38.Add( self.end_tPicker, 0, wx.ALL|wx.EXPAND|wx.RIGHT, 5 )

		bSizer39 = wx.BoxSizer( wx.VERTICAL )

		self.Date_calendar = wx.adv.CalendarCtrl( Ceck_Sizer1.GetStaticBox(), wx.ID_ANY, wx.DefaultDateTime, wx.DefaultPosition, wx.DefaultSize, wx.adv.CAL_MONDAY_FIRST|wx.adv.CAL_SEQUENTIAL_MONTH_SELECTION|wx.adv.CAL_SHOW_HOLIDAYS|wx.adv.CAL_SHOW_SURROUNDING_WEEKS )
		bSizer39.Add( self.Date_calendar, 1, wx.ALL|wx.EXPAND|wx.LEFT, 5 )


		bSizer38.Add( bSizer39, 1, wx.EXPAND, 5 )


		Ceck_Sizer1.Add( bSizer38, 0, wx.EXPAND, 5 )

		self.XML_ListCtrl = wx.ListCtrl( Ceck_Sizer1.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LC_ALIGN_LEFT|wx.LC_REPORT )
		Ceck_Sizer1.Add( self.XML_ListCtrl, 1, wx.ALL|wx.EXPAND|wx.LEFT, 5 )


		Param_Sizer1.Add( Ceck_Sizer1, 1, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		Logger_Sizer1 = wx.BoxSizer( wx.VERTICAL )

		self.bto_verificar_xml = wx.Button( self.XML_panel, wx.ID_ANY, u"Verificar", wx.DefaultPosition, wx.DefaultSize, 0 )
		Logger_Sizer1.Add( self.bto_verificar_xml, 0, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		self.xml_log_textCtrl = wx.TextCtrl( self.XML_panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL|wx.TE_MULTILINE|wx.TE_READONLY )
		Logger_Sizer1.Add( self.xml_log_textCtrl, 1, wx.ALL|wx.EXPAND, 5 )


		Param_Sizer1.Add( Logger_Sizer1, 1, wx.EXPAND, 5 )


		XMLmSizer1.Add( Param_Sizer1, 1, wx.EXPAND, 5 )

		XML_viewer_sizer = wx.BoxSizer( wx.VERTICAL )

		Count_Sizer = wx.BoxSizer( wx.HORIZONTAL )

		Search_BSizer = wx.StaticBoxSizer( wx.StaticBox( self.XML_panel, wx.ID_ANY, u"Elementos de busqueda" ), wx.HORIZONTAL )

		self.XML_searchCtrl = wx.SearchCtrl( Search_BSizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 200,-1 ), 0 )
		self.XML_searchCtrl.ShowSearchButton( True )
		self.XML_searchCtrl.ShowCancelButton( False )
		Search_BSizer.Add( self.XML_searchCtrl, 1, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		self.search_textCtrl = wx.TextCtrl( Search_BSizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 150,-1 ), wx.TE_READONLY )
		Search_BSizer.Add( self.search_textCtrl, 0, wx.ALL|wx.EXPAND|wx.LEFT, 5 )


		Count_Sizer.Add( Search_BSizer, 1, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		Verif_BSizer = wx.StaticBoxSizer( wx.StaticBox( self.XML_panel, wx.ID_ANY, u"Elementos de validaciones" ), wx.HORIZONTAL )

		verif_cBoxChoices = []
		self.verif_cBox = wx.ComboBox( Verif_BSizer.GetStaticBox(), wx.ID_ANY, u"Validaciones", wx.DefaultPosition, wx.DefaultSize, verif_cBoxChoices, 0 )
		Verif_BSizer.Add( self.verif_cBox, 0, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		self.verif_textCtrl = wx.TextCtrl( Verif_BSizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 150,-1 ), wx.TE_READONLY )
		Verif_BSizer.Add( self.verif_textCtrl, 0, wx.ALL, 5 )


		Count_Sizer.Add( Verif_BSizer, 0, wx.ALL|wx.EXPAND|wx.LEFT, 5 )


		XML_viewer_sizer.Add( Count_Sizer, 0, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		self.XML_TextCtrl = wx.stc.StyledTextCtrl( self.XML_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL|wx.VSCROLL)
		self.XML_TextCtrl.SetUseTabs ( True )
		self.XML_TextCtrl.SetTabWidth ( 4 )
		self.XML_TextCtrl.SetIndent ( 4 )
		self.XML_TextCtrl.SetTabIndents( True )
		self.XML_TextCtrl.SetBackSpaceUnIndents( True )
		self.XML_TextCtrl.SetViewEOL( False )
		self.XML_TextCtrl.SetViewWhiteSpace( False )
		self.XML_TextCtrl.SetMarginWidth( 2, 0 )
		self.XML_TextCtrl.SetIndentationGuides( True )
		self.XML_TextCtrl.SetReadOnly( False );
		self.XML_TextCtrl.SetMarginWidth( 1, 0 )
		self.XML_TextCtrl.SetMarginType( 0, wx.stc.STC_MARGIN_NUMBER );
		self.XML_TextCtrl.SetMarginWidth( 0, self.XML_TextCtrl.TextWidth( wx.stc.STC_STYLE_LINENUMBER, "_99999" ) )
		self.XML_TextCtrl.MarkerDefine( wx.stc.STC_MARKNUM_FOLDER, wx.stc.STC_MARK_BOXPLUS )
		self.XML_TextCtrl.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDER, wx.BLACK)
		self.XML_TextCtrl.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDER, wx.WHITE)
		self.XML_TextCtrl.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.stc.STC_MARK_BOXMINUS )
		self.XML_TextCtrl.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.BLACK )
		self.XML_TextCtrl.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.WHITE )
		self.XML_TextCtrl.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERSUB, wx.stc.STC_MARK_EMPTY )
		self.XML_TextCtrl.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEREND, wx.stc.STC_MARK_BOXPLUS )
		self.XML_TextCtrl.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEREND, wx.BLACK )
		self.XML_TextCtrl.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEREND, wx.WHITE )
		self.XML_TextCtrl.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.stc.STC_MARK_BOXMINUS )
		self.XML_TextCtrl.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.BLACK)
		self.XML_TextCtrl.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.WHITE)
		self.XML_TextCtrl.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERMIDTAIL, wx.stc.STC_MARK_EMPTY )
		self.XML_TextCtrl.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERTAIL, wx.stc.STC_MARK_EMPTY )
		self.XML_TextCtrl.SetSelBackground( True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT ) )
		self.XML_TextCtrl.SetSelForeground( True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT ) )
		self.XML_TextCtrl.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )
		self.XML_TextCtrl.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_INFOBK ) )

		XML_viewer_sizer.Add( self.XML_TextCtrl, 1, wx.EXPAND |wx.ALL, 5 )


		XMLmSizer1.Add( XML_viewer_sizer, 1, wx.EXPAND, 5 )


		self.XML_panel.SetSizer( XMLmSizer1 )
		self.XML_panel.Layout()
		XMLmSizer1.Fit( self.XML_panel )
		self.main_notebook1.AddPage( self.XML_panel, u"XML", False )
		self.RAW_panel = wx.Panel( self.main_notebook1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		RAWmSizer = wx.BoxSizer( wx.HORIZONTAL )

		self.RAW_nb = wx.Notebook( self.RAW_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.RAWParameters_Panel = wx.Panel( self.RAW_nb, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.RAWParameters_Panel.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
		self.RAWParameters_Panel.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

		RAWParam_Sizer = wx.BoxSizer( wx.HORIZONTAL )

		RAWParam_Sizer1 = wx.BoxSizer( wx.VERTICAL )

		self.logo_cen3 = wx.StaticBitmap( self.RAWParameters_Panel, wx.ID_ANY, wx.Bitmap( u"D:\\E0139.CENACE\\My Documents\\Mis imágenes\\iconos\\CENACE-logo-completo.png", wx.BITMAP_TYPE_ANY ), wx.DefaultPosition, wx.DefaultSize, 0 )
		RAWParam_Sizer1.Add( self.logo_cen3, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

		Data_Sizer112 = wx.StaticBoxSizer( wx.StaticBox( self.RAWParameters_Panel, wx.ID_ANY, u"Parámetros de control" ), wx.HORIZONTAL )

		_sistemaChoices = [u"SIN", u"BCA", u"BCS"]
		self._sistema = wx.CheckListBox( Data_Sizer112.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, _sistemaChoices, wx.LB_SINGLE|wx.BORDER_NONE )
		self._sistema.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

		Data_Sizer112.Add( self._sistema, 1, wx.ALL|wx.EXPAND|wx.LEFT, 10 )

		analisisChoices = [u"Seleccionar ultimo RAW de SP7", u"Seleccionar ultimo RAW de ABB", u"Seleccionar RAW"]
		self.analisis = wx.CheckListBox( Data_Sizer112.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, analisisChoices, 0|wx.BORDER_NONE )
		self.analisis.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

		Data_Sizer112.Add( self.analisis, 1, wx.ALL|wx.EXPAND|wx.LEFT, 5 )


		RAWParam_Sizer1.Add( Data_Sizer112, 0, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		Data_Sizer11 = wx.StaticBoxSizer( wx.StaticBox( self.RAWParameters_Panel, wx.ID_ANY, u"Seleccionar RAW 1" ), wx.VERTICAL )

		self.RAW_pathSel1 = wx.DirPickerCtrl( Data_Sizer11.GetStaticBox(), wx.ID_ANY, wx.EmptyString, u"Seleccionar carpeta", wx.DefaultPosition, wx.DefaultSize, wx.DIRP_DEFAULT_STYLE|wx.DIRP_DIR_MUST_EXIST )
		Data_Sizer11.Add( self.RAW_pathSel1, 1, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		self.m_checkBox9 = wx.CheckBox( Data_Sizer11.GetStaticBox(), wx.ID_ANY, u"El RAW es de ABB", wx.DefaultPosition, wx.DefaultSize, 0 )
		Data_Sizer11.Add( self.m_checkBox9, 1, wx.ALL|wx.EXPAND|wx.LEFT, 5 )


		RAWParam_Sizer1.Add( Data_Sizer11, 0, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		Data_Sizer111 = wx.StaticBoxSizer( wx.StaticBox( self.RAWParameters_Panel, wx.ID_ANY, u"Seleccionar RAW 2" ), wx.VERTICAL )

		self.RAW_pathSel2 = wx.DirPickerCtrl( Data_Sizer111.GetStaticBox(), wx.ID_ANY, u"Seleccionar RAW a comparar", u"Seleccionar carpeta", wx.DefaultPosition, wx.DefaultSize, wx.DIRP_DEFAULT_STYLE|wx.DIRP_DIR_MUST_EXIST )
		Data_Sizer111.Add( self.RAW_pathSel2, 1, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		self.m_checkBox91 = wx.CheckBox( Data_Sizer111.GetStaticBox(), wx.ID_ANY, u"El RAW es de ABB", wx.DefaultPosition, wx.DefaultSize, 0 )
		Data_Sizer111.Add( self.m_checkBox91, 1, wx.ALL|wx.EXPAND|wx.LEFT, 5 )


		RAWParam_Sizer1.Add( Data_Sizer111, 0, wx.ALL|wx.EXPAND, 5 )

		self.bto_leer_RAWs = wx.Button( self.RAWParameters_Panel, wx.ID_ANY, u"Leer RWAs", wx.DefaultPosition, wx.DefaultSize, 0 )
		RAWParam_Sizer1.Add( self.bto_leer_RAWs, 0, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		Data_Sizer1111 = wx.StaticBoxSizer( wx.StaticBox( self.RAWParameters_Panel, wx.ID_ANY, u"Validaciones" ), wx.VERTICAL )

		self.m_checkBox911 = wx.CheckBox( Data_Sizer1111.GetStaticBox(), wx.ID_ANY, u"Exportar reporte", wx.DefaultPosition, wx.DefaultSize, 0 )
		Data_Sizer1111.Add( self.m_checkBox911, 0, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		self.m_button18111 = wx.Button( Data_Sizer1111.GetStaticBox(), wx.ID_ANY, u"Comparar RAWs", wx.DefaultPosition, wx.DefaultSize, 0 )
		Data_Sizer1111.Add( self.m_button18111, 0, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		self.m_button1811 = wx.Button( Data_Sizer1111.GetStaticBox(), wx.ID_ANY, u"Comparar parámetros", wx.DefaultPosition, wx.DefaultSize, 0 )
		Data_Sizer1111.Add( self.m_button1811, 0, wx.ALL|wx.EXPAND|wx.LEFT, 5 )


		RAWParam_Sizer1.Add( Data_Sizer1111, 1, wx.ALL|wx.EXPAND, 5 )


		RAWParam_Sizer.Add( RAWParam_Sizer1, 1, wx.EXPAND, 5 )

		self.raw_log_textCtrl = wx.TextCtrl( self.RAWParameters_Panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE|wx.TE_READONLY )
		RAWParam_Sizer.Add( self.raw_log_textCtrl, 1, wx.ALL|wx.EXPAND|wx.LEFT, 5 )


		self.RAWParameters_Panel.SetSizer( RAWParam_Sizer )
		self.RAWParameters_Panel.Layout()
		RAWParam_Sizer.Fit( self.RAWParameters_Panel )
		self.RAW_nb.AddPage( self.RAWParameters_Panel, u"Comparación", False )
		self.RAWDiagram_Panel = wx.Panel( self.RAW_nb, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.RAWDiagram_Panel.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

		Diagram_Sizer = wx.BoxSizer( wx.VERTICAL )

		RAW_Sizer = wx.BoxSizer( wx.HORIZONTAL )

		Portada_BSizer = wx.BoxSizer( wx.VERTICAL )

		self.logo_cen31 = wx.StaticBitmap( self.RAWDiagram_Panel, wx.ID_ANY, wx.Bitmap( u"D:\\E0139.CENACE\\My Documents\\Mis imágenes\\iconos\\CENACE-logo-completo.png", wx.BITMAP_TYPE_ANY ), wx.DefaultPosition, wx.DefaultSize, 0 )
		Portada_BSizer.Add( self.logo_cen31, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

		Bus_BSizer = wx.StaticBoxSizer( wx.StaticBox( self.RAWDiagram_Panel, wx.ID_ANY, u"Buses" ), wx.VERTICAL )

		self.RAW_searchCtrl = wx.SearchCtrl( Bus_BSizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_PROCESS_ENTER )
		self.RAW_searchCtrl.ShowSearchButton( True )
		self.RAW_searchCtrl.ShowCancelButton( False )
		self.RAW_searchCtrl.Enable( False )

		Bus_BSizer.Add( self.RAW_searchCtrl, 0, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		bSizer29 = wx.BoxSizer( wx.VERTICAL )

		self.elm_panel = wx.Panel( Bus_BSizer.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,100 ), wx.TAB_TRAVERSAL )
		bSizer29.Add( self.elm_panel, 1, wx.EXPAND |wx.ALL, 5 )


		Bus_BSizer.Add( bSizer29, 1, wx.EXPAND, 5 )


		Portada_BSizer.Add( Bus_BSizer, 1, wx.ALL|wx.EXPAND|wx.LEFT, 5 )


		RAW_Sizer.Add( Portada_BSizer, 1, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		mRama_textSizer = wx.BoxSizer( wx.VERTICAL )

		self.rama_Stext = wx.StaticText( self.RAWDiagram_Panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_LEFT )
		self.rama_Stext.Wrap( -1 )

		self.rama_Stext.SetFont( wx.Font( 14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString ) )

		mRama_textSizer.Add( self.rama_Stext, 0, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		Branch_BSizer = wx.StaticBoxSizer( wx.StaticBox( self.RAWDiagram_Panel, wx.ID_ANY, u"Ramas de los buses" ), wx.VERTICAL )

		raw_listSizer = wx.BoxSizer( wx.HORIZONTAL )

		RAW1_listBSizer = wx.StaticBoxSizer( wx.StaticBox( Branch_BSizer.GetStaticBox(), wx.ID_ANY, u"RAW 1" ), wx.VERTICAL )

		self.RAW1_listCtrl = wx.ListCtrl( RAW1_listBSizer.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LC_ALIGN_LEFT|wx.LC_AUTOARRANGE|wx.LC_REPORT|wx.VSCROLL )
		RAW1_listBSizer.Add( self.RAW1_listCtrl, 1, wx.ALL|wx.EXPAND|wx.LEFT, 5 )


		raw_listSizer.Add( RAW1_listBSizer, 1, wx.ALL|wx.EXPAND|wx.LEFT, 5 )

		RAW2_listBSizer = wx.StaticBoxSizer( wx.StaticBox( Branch_BSizer.GetStaticBox(), wx.ID_ANY, u"RAW 2" ), wx.VERTICAL )

		self.RAW2_listCtrl = wx.ListCtrl( RAW2_listBSizer.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LC_ALIGN_LEFT|wx.LC_AUTOARRANGE|wx.LC_REPORT|wx.VSCROLL )
		RAW2_listBSizer.Add( self.RAW2_listCtrl, 1, wx.ALL|wx.EXPAND|wx.LEFT, 5 )


		raw_listSizer.Add( RAW2_listBSizer, 1, wx.ALL|wx.EXPAND|wx.LEFT, 5 )


		Branch_BSizer.Add( raw_listSizer, 1, wx.EXPAND, 5 )

		self.subRama_Stext = wx.StaticText( Branch_BSizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.subRama_Stext.Wrap( -1 )

		self.subRama_Stext.SetFont( wx.Font( 12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, True, wx.EmptyString ) )

		Branch_BSizer.Add( self.subRama_Stext, 0, wx.ALL|wx.EXPAND|wx.LEFT, 5 )


		mRama_textSizer.Add( Branch_BSizer, 1, wx.EXPAND, 5 )


		RAW_Sizer.Add( mRama_textSizer, 1, wx.EXPAND, 5 )


		Diagram_Sizer.Add( RAW_Sizer, 1, wx.EXPAND, 5 )

		Diag_Sizer = wx.BoxSizer( wx.HORIZONTAL )

		RAW1_BSizer = wx.StaticBoxSizer( wx.StaticBox( self.RAWDiagram_Panel, wx.ID_ANY, u"RAW 1" ), wx.VERTICAL )

		self.RAW1_panel = wx.Simplebook( RAW1_BSizer.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )

		RAW1_BSizer.Add( self.RAW1_panel, 1, wx.ALL|wx.EXPAND|wx.LEFT, 0 )


		Diag_Sizer.Add( RAW1_BSizer, 1, wx.EXPAND, 0 )

		RAW2_BSizer = wx.StaticBoxSizer( wx.StaticBox( self.RAWDiagram_Panel, wx.ID_ANY, u"RAW 2" ), wx.VERTICAL )

		self.RAW2_panel = wx.Simplebook( RAW2_BSizer.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )

		RAW2_BSizer.Add( self.RAW2_panel, 1, wx.EXPAND |wx.ALL, 5 )


		Diag_Sizer.Add( RAW2_BSizer, 1, wx.EXPAND, 5 )


		Diagram_Sizer.Add( Diag_Sizer, 1, wx.EXPAND, 5 )


		self.RAWDiagram_Panel.SetSizer( Diagram_Sizer )
		self.RAWDiagram_Panel.Layout()
		Diagram_Sizer.Fit( self.RAWDiagram_Panel )
		self.RAW_nb.AddPage( self.RAWDiagram_Panel, u"Diagrama de subestación", True )

		RAWmSizer.Add( self.RAW_nb, 1, wx.EXPAND, 5 )


		self.RAW_panel.SetSizer( RAWmSizer )
		self.RAW_panel.Layout()
		RAWmSizer.Fit( self.RAW_panel )
		self.main_notebook1.AddPage( self.RAW_panel, u"RAW", True )

		Sizer0.Add( self.main_notebook1, 1, wx.EXPAND, 5 )


		MainS.Add( Sizer0, 1, wx.EXPAND, 5 )


		self.SetSizer( MainS )
		self.Layout()
		MainS.Fit( self )
		self.main_menu = wx.MenuBar( 0 )
		self.m_menu_file = wx.Menu()
		self.m_menu_file_new = wx.MenuItem( self.m_menu_file, wx.ID_ANY, u"Nuevo"+ u"\t" + u"Ctrl+N", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu_file_new.SetBitmap( wx.NullBitmap )
		self.m_menu_file.Append( self.m_menu_file_new )

		self.m_menu_file_open = wx.MenuItem( self.m_menu_file, wx.ID_ANY, u"Abrir"+ u"\t" + u"Ctrl+O", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu_file_open.SetBitmap( wx.NullBitmap )
		self.m_menu_file.Append( self.m_menu_file_open )

		self.m_menu_file_save = wx.MenuItem( self.m_menu_file, wx.ID_ANY, u"Guardar"+ u"\t" + u"Ctrl+S", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu_file.Append( self.m_menu_file_save )

		self.m_menu_file_saveas = wx.MenuItem( self.m_menu_file, wx.ID_ANY, u"Guardar como"+ u"\t" + u"Ctrl+Shift+S", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu_file.Append( self.m_menu_file_saveas )

		self.m_menu_file.AppendSeparator()

		self.m_menu_file_exit = wx.MenuItem( self.m_menu_file, wx.ID_ANY, u"Salir"+ u"\t" + u"Alt+F4", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu_file_exit.SetBitmap( wx.NullBitmap )
		self.m_menu_file.Append( self.m_menu_file_exit )

		self.main_menu.Append( self.m_menu_file, u"Archivo" )

		self.m_menu_edit = wx.Menu()
		self.main_menu.Append( self.m_menu_edit, u"Editar" )

		self.menu_ayuda = wx.Menu()
		self.introduccion = wx.MenuItem( self.menu_ayuda, wx.ID_ANY, u"Introducción", wx.EmptyString, wx.ITEM_NORMAL )
		self.introduccion.SetBitmap( wx.Bitmap( u"D:\\E0139.CENACE\\My Documents\\Mis imágenes\\iconos\\info.png", wx.BITMAP_TYPE_ANY ) )
		self.menu_ayuda.Append( self.introduccion )

		self.queries = wx.MenuItem( self.menu_ayuda, wx.ID_ANY, u"Queries", wx.EmptyString, wx.ITEM_NORMAL )
		self.queries.SetBitmap( wx.Bitmap( u"D:\\E0139.CENACE\\My Documents\\Mis imágenes\\iconos\\info.png", wx.BITMAP_TYPE_ANY ) )
		self.menu_ayuda.Append( self.queries )

		self.main_menu.Append( self.menu_ayuda, u"Ayuda" )

		self.SetMenuBar( self.main_menu )

		self.statusBarRAW = self.CreateStatusBar( 1, wx.STB_SIZEGRIP, wx.ID_ANY )

		self.Centre( wx.BOTH )

		# Connect Events
		self.MAGE_pathSel.Bind( wx.EVT_DIRPICKER_CHANGED, self.Data_athSelectOnDirChanged )
		self.bto_preprocesar_archivos.Bind( wx.EVT_BUTTON, self.ProcCSV_buttonOnButtonClick )
		self.bto_verificar_mage.Bind( wx.EVT_BUTTON, self.Run_buttonOnButtonClick )
		self.Export_button.Bind( wx.EVT_BUTTON, self.Export_buttonOnButtonClick )
		self.RAW_searchCtrl.Bind( wx.EVT_TEXT_ENTER, self.RAW_searchCtrlOnTextEnter )
		self.Bind( wx.EVT_MENU, self.m_menu_file_newOnMenuSelection, id = self.m_menu_file_new.GetId() )
		self.Bind( wx.EVT_MENU, self.m_menu_file_openOnMenuSelection, id = self.m_menu_file_open.GetId() )
		self.Bind( wx.EVT_MENU, self.m_menu_file_saveOnMenuSelection, id = self.m_menu_file_save.GetId() )
		self.Bind( wx.EVT_MENU, self.m_menu_file_saveasOnMenuSelection, id = self.m_menu_file_saveas.GetId() )
		self.Bind( wx.EVT_MENU, self.m_menu_file_exitOnMenuSelection, id = self.m_menu_file_exit.GetId() )

	def __del__( self ):
		pass


	# Virtual event handlers, override them in your derived class
	def Data_athSelectOnDirChanged( self, event ):
		event.Skip()

	def ProcCSV_buttonOnButtonClick( self, event ):
		event.Skip()

	def Run_buttonOnButtonClick( self, event ):
		event.Skip()

	def Export_buttonOnButtonClick( self, event ):
		event.Skip()

	def RAW_searchCtrlOnTextEnter( self, event ):
		event.Skip()

	def m_menu_file_newOnMenuSelection( self, event ):
		event.Skip()

	def m_menu_file_openOnMenuSelection( self, event ):
		event.Skip()

	def m_menu_file_saveOnMenuSelection( self, event ):
		event.Skip()

	def m_menu_file_saveasOnMenuSelection( self, event ):
		event.Skip()

	def m_menu_file_exitOnMenuSelection( self, event ):
		event.Skip()


