import {Component, Inject, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef} from '@angular/material';

@Component({
  selector: 'app-options',
  templateUrl: './options.component.html',
  styleUrls: ['./options.component.css']
})
export class OptionsComponent implements OnInit
{
  /* The options title */
  title = '';


  /**
   * default constructor
   *
   * @param dialogRef dependency injection
   * @param data Contains title and options
   */
  constructor(public dialogRef: MatDialogRef<OptionsComponent>, @Inject(MAT_DIALOG_DATA) public data: object)
  {
    this.title = this.data['title'];
  }


  /**
   * Initialize the component
   */
  ngOnInit()
  {
  }


  /**
   * Select all options
   */
  selectAll(): void
  {
    for (let i = 0; i < this.data['list']['options'].length; i++)
    {
      this.data['list']['options'][i].selected = true;
    }
  }


  /**
   * Unselect all options
   */
  unselectAll(): void
  {
    for (let i = 0; i < this.data['list']['options'].length; i++)
    {
      this.data['list']['options'][i].selected = false;
    }
  }


  /**
   * Invert the current selection
   */
  invertSelection(): void
  {
    for (let i = 0; i < this.data['list']['options'].length; i++)
    {
      this.data['list']['options'][i].selected = !this.data['list']['options'][i].selected;
    }
  }


  /**
   * Close the dialog
   */
  closeDialog(): void
  {
    this.dialogRef.close();
  }
}
