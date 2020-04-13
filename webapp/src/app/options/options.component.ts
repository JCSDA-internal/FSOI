import {Component, Inject, OnInit, OnDestroy} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef} from '@angular/material';

@Component({
  selector: 'app-options',
  templateUrl: './options.component.html',
  styleUrls: ['./options.component.css']
})
export class OptionsComponent implements OnInit, OnDestroy
{
  /* The options title */
  title = '';
  selectMultiple = true;
  selectedOption = null;


  /**
   * default constructor
   *
   * @param dialogRef dependency injection
   * @param data Contains title and options
   */
  constructor(public dialogRef: MatDialogRef<OptionsComponent>, @Inject(MAT_DIALOG_DATA) public data: object)
  {
    this.title = this.data['title'];
    this.selectMultiple = this.data['selectMultiple'];

    if (! this.selectMultiple)
    {
      this.selectOne();
    }
  }


  /**
   * Initialize the component
   */
  ngOnInit()
  {
  }


  /**
   * Update the list of options to match the selection
   */
  ngOnDestroy()
  {
    if (!this.selectMultiple)
    {
      for (let i = 0; i < this.data['list']['options'].length; i++)
      {
        this.data['list']['options'][i]['selected'] = (this.data['list']['options'][i]['name'] === this.selectedOption);
      }
    }
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
   * Make sure that only one option is selected
   */
  selectOne(): void
  {
    let oneSelected = false;

    for (let i = 0; i < this.data['list']['options'].length; i++)
    {
      if (oneSelected)
      {
        this.data['list']['options'][i].selected = false;
      }
      else
      {
        oneSelected = this.data['list']['options'][i].selected;
        if (oneSelected)
        {
          this.selectedOption = this.data['list']['options'][i]['name'];
        }
      }
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
