object Form1: TForm1
  Left = 175
  Top = 367
  Width = 932
  Height = 519
  Caption = 'Form1'
  Color = clBtnFace
  Font.Charset = DEFAULT_CHARSET
  Font.Color = clWindowText
  Font.Height = -11
  Font.Name = 'MS Sans Serif'
  Font.Style = []
  OldCreateOrder = False
  PixelsPerInch = 96
  TextHeight = 13
  object Memo1: TMemo
    Left = 464
    Top = 8
    Width = 441
    Height = 441
    Font.Charset = DEFAULT_CHARSET
    Font.Color = clWindowText
    Font.Height = -11
    Font.Name = 'Arial'
    Font.Pitch = fpFixed
    Font.Style = []
    Lines.Strings = (
      'Memo1')
    ParentFont = False
    ScrollBars = ssVertical
    TabOrder = 0
  end
  object StringGrid1: TStringGrid
    Left = 8
    Top = 8
    Width = 449
    Height = 441
    ColCount = 25
    DefaultColWidth = 15
    DefaultRowHeight = 15
    FixedCols = 0
    RowCount = 25
    FixedRows = 0
    TabOrder = 1
    OnDrawCell = StringGrid1DrawCell
  end
  object Timer1: TTimer
    Interval = 100
    OnTimer = Timer1Timer
    Left = 424
    Top = 16
  end
end
