package Demo;

public class Computer {
	private String MainBoard;
	private String CPU;
	private String Memory;
	private String HardDisk;
	private String VideoCard;
	
	public String getMainBoard(){
		return MainBoard;
	}	
	public void setMainBoard(String str){
		MainBoard=str;
	}
	
	public String getCPU(){
		return CPU;
	}	
	public void setCPU(String str){
		CPU=str;
	}
	
	public String getMemory(){
		return Memory;
	}	
	public void setMemory(String str){
		Memory=str;
	}
	
	public String getHardDisk(){
		return HardDisk;
	}	
	public void setHardDisk(String str){
		HardDisk=str;
	}
	
	public String getVideoCard(){
		return VideoCard;
	}	
	public void setVideoCard(String str){
		VideoCard=str;
	}
	
	public void ShowSysInfo(){
		System.out.println("=======主机部件配置信息=======");
		System.out.println("主板类型："+MainBoard);
		System.out.println("CPU类型："+CPU);
		System.out.println("内存类型："+Memory);
		System.out.println("硬盘类型："+HardDisk);
		System.out.println("显卡类型："+VideoCard);
	}

}
