import {Component, Inject, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef} from '@angular/material';

@Component({
  selector: 'app-options',
  templateUrl: './options.component.html',
  styleUrls: ['./options.component.css']
})
export class OptionsComponent implements OnInit
{
  title = '';

  constructor(public dialogRef: MatDialogRef<OptionsComponent>, @Inject(MAT_DIALOG_DATA) public data: object)
  {
    this.title = this.data['title'];
  }

  ngOnInit()
  {
  }

  selectAll(): void
  {
    for (let i = 0; i < this.data['list']['options'].length; i++)
    {
      this.data['list']['options'][i].selected = true;
    }
  }

  unselectAll(): void
  {
    for (let i = 0; i < this.data['list']['options'].length; i++)
    {
      this.data['list']['options'][i].selected = false;
    }
  }

  invertSelection(): void
  {
    for (let i = 0; i < this.data['list']['options'].length; i++)
    {
      this.data['list']['options'][i].selected = !this.data['list']['options'][i].selected;
    }
  }

  closeDialog(): void
  {
    this.dialogRef.close();
  }
}
