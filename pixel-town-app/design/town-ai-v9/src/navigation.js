export class PublicNavigation {
 constructor(grid){Object.assign(this,grid);this.valid=new Set(grid.cells)}
 index(x,z){const c=Math.round((x-this.origin[0])/this.spacing),r=Math.round((z-this.origin[1])/this.spacing);return c>=0&&r>=0&&c<this.cols&&r<this.rows?r*this.cols+c:-1}
 point(i){return [this.origin[0]+i%this.cols*this.spacing,this.heights[i]||0,this.origin[1]+Math.floor(i/this.cols)*this.spacing]}
 nearest(point,max=.76){const i=this.index(point[0],point[2]);let best=null,distance=max;const [x,,z]=point;for(let dz=-2;dz<=2;dz++)for(let dx=-2;dx<=2;dx++){const n=i+dz*this.cols+dx;if(!this.valid.has(n))continue;const p=this.point(n),d=Math.hypot(p[0]-x,p[2]-z);if(d<=distance){distance=d;best=n}}return best}
 path(from,to,blocked=new Set()){
  const start=this.nearest(from),end=this.nearest(to,.26);if(start===null||end===null)throw new Error('目的地或起点不在已验证的室外步道上');
  if(blocked.has(end)&&end!==start)throw new Error('目的地被其他角色占用');
  const parent=new Int32Array(this.cols*this.rows).fill(-2),queue=new Int32Array(this.valid.size);let head=0,tail=0;queue[tail++]=start;parent[start]=-1;
  while(head<tail){const i=queue[head++];if(i===end)break;const col=i%this.cols;
   for(const n of [col?i-1:-1,col<this.cols-1?i+1:-1,i-this.cols,i+this.cols])if(this.valid.has(n)&&parent[n]===-2&&(!blocked.has(n)||n===start)&&Math.abs((this.heights[i]||0)-(this.heights[n]||0))<=this.maxStep+.001){parent[n]=i;queue[tail++]=n;}
  }
  if(parent[end]===-2)throw new Error('公共步道没有可达路径，或通道正被占用');
  const route=[];for(let i=end;i!==-1;i=parent[i])route.push(this.point(i));return route.reverse();
 }
}
