unit Unit1;

interface

uses
  Windows, Messages, SysUtils, Variants, Classes, Graphics, Controls, Forms,
  Dialogs, ExtCtrls, StdCtrls, Grids;

type
  TForm1 = class(TForm)
    Memo1: TMemo;
    Timer1: TTimer;
    StringGrid1: TStringGrid;
    procedure Timer1Timer(Sender: TObject);
     procedure StringGrid1DrawCell(Sender: TObject; ACol, ARow: Integer;
      Rect: TRect; State: TGridDrawState);
  private
    { Private declarations }
  public
    { Public declarations }
  end;

var
  Form1: TForm1;

implementation

{$R *.dfm}

procedure TForm1.Timer1Timer(Sender: TObject);
var col , row : Integer;
var line , cma : string;
begin
try
cma := ',';
Memo1.Lines.LoadFromFile('quickprint.txt');

for row := 0 to Memo1.Lines.Count do
  begin
  line := #2588 + Memo1.Lines.Strings[row];
  for col := length(line) downto 2 do
    begin
    Insert(cma , line , col);
    end;
  StringGrid1.Rows[row].CommaText := line;
  end;

  except
  col := 9;
  end;
end;

procedure TForm1.StringGrid1DrawCell(Sender: TObject; ACol, ARow: Integer;
  Rect: TRect; State: TGridDrawState);
begin
if StringGrid1.Cells[ACol,ARow] = 'x' then
  begin
  //StringGrid1.Cells[ACol,ARow] := 'X';
  //StringGrid1.Color := clBlack;
  //self.Canvas.Brush.Color := clBlack;
  //State := [gdSelected	,gdFocused]	;
  //StringGrid1.Canvas.Font.Color := clWhite;
  //StringGrid1.Canvas.Font.Color := clBlack;
  //StringGrid1.Canvas.Brush.Color := clBlack;
  //StringGrid1.CellRect(ACol,ARow)
  //Canvas.Brush.Color := clRed;
//   := clBlack;
   //DrawGrid1->Canvas->Brush->Color = clBlack;

   end


end;

end.
