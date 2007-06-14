/* begin WINE */
/* Dialog styles */
#define DS_ABSALIGN     0x0001
#define DS_SYSMODAL     0x0002
#define DS_3DLOOK       0x0004  /* win95 */
#define DS_FIXEDSYS     0x0008  /* win95 */
#define DS_NOFAILCREATE     0x0010  /* win95 */
#define DS_LOCALEDIT        0x0020
#define DS_SETFONT      0x0040
#define DS_MODALFRAME       0x0080
#define DS_NOIDLEMSG        0x0100
#define DS_SETFOREGROUND    0x0200  /* win95 */
#define DS_CONTROL      0x0400  /* win95 */
#define DS_CENTER       0x0800  /* win95 */
#define DS_CENTERMOUSE      0x1000  /* win95 */
#define DS_CONTEXTHELP      0x2000  /* win95 */



/* Window Styles */
#define WS_OVERLAPPED    0x00000000L
#define WS_POPUP         0x80000000L
#define WS_CHILD         0x40000000L
#define WS_MINIMIZE      0x20000000L
#define WS_VISIBLE       0x10000000L
#define WS_DISABLED      0x08000000L
#define WS_CLIPSIBLINGS  0x04000000L
#define WS_CLIPCHILDREN  0x02000000L
#define WS_MAXIMIZE      0x01000000L
#define WS_CAPTION       0x00C00000L
#define WS_BORDER        0x00800000L
#define WS_DLGFRAME      0x00400000L
#define WS_VSCROLL       0x00200000L
#define WS_HSCROLL       0x00100000L
#define WS_SYSMENU       0x00080000L
#define WS_THICKFRAME    0x00040000L
#define WS_GROUP         0x00020000L
#define WS_TABSTOP       0x00010000L
#define WS_MINIMIZEBOX   0x00020000L
#define WS_MAXIMIZEBOX   0x00010000L
#define WS_TILED         WS_OVERLAPPED
#define WS_ICONIC        WS_MINIMIZE
#define WS_SIZEBOX       WS_THICKFRAME
#define WS_OVERLAPPEDWINDOW (WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_THICKFRAME| WS_MINIMIZEBOX | WS_MAXIMIZEBOX)
#define WS_POPUPWINDOW (WS_POPUP | WS_BORDER | WS_SYSMENU)
#define WS_CHILDWINDOW (WS_CHILD)
#define WS_TILEDWINDOW (WS_OVERLAPPEDWINDOW)

/* Window extended styles */
#define WS_EX_DLGMODALFRAME    0x00000001L
#define WS_EX_DRAGDETECT       0x00000002L
#define WS_EX_NOPARENTNOTIFY   0x00000004L
#define WS_EX_TOPMOST          0x00000008L
#define WS_EX_ACCEPTFILES      0x00000010L
#define WS_EX_TRANSPARENT      0x00000020L

/* New Win95/WinNT4 styles */
#define WS_EX_MDICHILD         0x00000040L
#define WS_EX_TOOLWINDOW       0x00000080L
#define WS_EX_WINDOWEDGE       0x00000100L
#define WS_EX_CLIENTEDGE       0x00000200L
#define WS_EX_CONTEXTHELP      0x00000400L
#define WS_EX_RIGHT            0x00001000L
#define WS_EX_LEFT             0x00000000L
#define WS_EX_RTLREADING       0x00002000L
#define WS_EX_LTRREADING       0x00000000L
#define WS_EX_LEFTSCROLLBAR    0x00004000L
#define WS_EX_RIGHTSCROLLBAR   0x00000000L
#define WS_EX_CONTROLPARENT    0x00010000L
#define WS_EX_STATICEDGE       0x00020000L
#define WS_EX_APPWINDOW        0x00040000L

#define WS_EX_OVERLAPPEDWINDOW (WS_EX_WINDOWEDGE|WS_EX_CLIENTEDGE)
#define WS_EX_PALETTEWINDOW    (WS_EX_WINDOWEDGE|WS_EX_TOOLWINDOW|WS_EX_TOPMOST)

/* end WINE */

typedef struct _DialogBoxHeader 
	{
	U32 lStyle;
	U32 lExtendedStyle;     // new for NT
	U16 NumberOfItems;
	U16 x;
	U16 y;
	U16 cx;
	U16 cy;
	U16 *MenuName;
	U16 *ClassName;
	U16 *szCaption;
	U16 wPointSize;         // Only here if FONT set for dialog
	U16 *szFontName;       // This too
	} DialogBoxHeader;

void wvGetDialogBoxHeader(DialogBoxHeader *dlg,FILE *fd);
void wvFreeDialogBoxHeader(DialogBoxHeader *dlg);


typedef struct _ControlData 
	{
	U32 lStyle;
	U32 lExtendedStyle;
	U16 x;
	U16 y;
	U16 cx;
	U16 cy;
	U16 wId;
	U16 *ClassId;
	U16 *Text;
	U16 nExtraStuff;
	} ControlData;

void wvGetControlData(ControlData *ctl,FILE *fd);
void wvFreeControlData(ControlData *ctl);

void wvDialogBoxHeaderGtk(DialogBoxHeader *dlg,FILE *out);
void wvControlDataGtk(ControlData *ctl,FILE *out);



