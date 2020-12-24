import {Component, Inject, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef} from '@angular/material/dialog';

@Component({
  selector: 'app-message',
  templateUrl: './message.component.html',
  styleUrls: ['./message.component.css']
})
export class MessageComponent implements OnInit
{
  /* message title */
  title = '';

  /* message text */
  message = '';

  /* show copy button flag */
  showCopyButton = true;


  /**
   * Constructor
   *
   * @param dialogRef dependency injection
   * @param data Includes title and message
   */
  constructor(public dialogRef: MatDialogRef<MessageComponent>, @Inject(MAT_DIALOG_DATA) public data: object)
  {
    this.title = data['title'];
    this.message = data['message'];
    if (data['showCopyButton'] !== undefined)
    {
      this.showCopyButton = Boolean(data['showCopyButton']);
    }
  }


  /**
   * Initialize the component
   */
  ngOnInit()
  {
  }


  /**
   * Close the dialog
   */
  closeDialog(): void
  {
    this.dialogRef.close();
  }


  /**
   * Copy message to clipboard
   */
  copyToClipboard(): void
  {
    const selBox = document.createElement('textarea');
    selBox.style.position = 'fixed';
    selBox.style.left = '0';
    selBox.style.top = '0';
    selBox.style.opacity = '0';
    selBox.value = this.message;
    document.body.appendChild(selBox);
    selBox.focus();
    selBox.select();
    document.execCommand('copy');
    document.body.removeChild(selBox);
  }
}
